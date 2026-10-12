"""Which buttons a user should see for a request (state-aware rendering).

HCI constraint 3: buttons for invalid transitions must not appear at all, not merely be disabled.
Pure function of the lifecycle state, the viewer's role and the condition reports so far; the
database still re-checks every command, so this only shapes the UI. Names match the REST
endpoints: accept, decline, cancel, handover_checklist, handover_confirm, initiate_return,
return_checklist, return_confirm.
"""

from collections.abc import Mapping
from datetime import datetime
from typing import Any

PENDING = {"REQUEST_CREATED", "LOCALITY_CHECKED", "HELD_FOR_REVIEW", "ASSESSED"}


def _created(report: Mapping[str, Any] | None) -> datetime | None:
    return report["created_at"] if report else None


def _borrower_must_confirm(
    lender: Mapping[str, Any] | None, borrower: Mapping[str, Any] | None
) -> bool:
    """The borrower's confirmation counts only if made after the lender's latest checklist."""
    if lender is None:
        return False
    if borrower is None:
        return True
    return bool(_created(borrower) < _created(lender))  # type: ignore[operator]


def available_actions(
    state: str | None,
    role: str | None,
    reports: Mapping[tuple[str, str], Mapping[str, Any]],
) -> list[str]:
    """`reports` maps (phase, reporter_role) -> latest condition report, e.g. ("HANDOVER", "LENDER")."""
    if state is None or role is None:
        return []
    h_l, h_b = reports.get(("HANDOVER", "LENDER")), reports.get(("HANDOVER", "BORROWER"))
    r_l, r_b = reports.get(("RETURN", "LENDER")), reports.get(("RETURN", "BORROWER"))
    actions: list[str] = []
    if role == "LENDER":
        if state == "ASSESSED":
            actions = ["accept", "decline"]
        elif state == "ACCEPTED":
            actions = ["handover_checklist"]
        elif state == "RETURN_INITIATED" and r_l is None:
            actions = ["return_checklist"]
    elif role == "BORROWER":
        if state in PENDING:
            actions = ["cancel"]
        elif state == "ACCEPTED" and _borrower_must_confirm(h_l, h_b):
            actions = ["handover_confirm"]
        elif state == "ACTIVE":
            actions = ["initiate_return"]
        elif state == "RETURN_INITIATED" and _borrower_must_confirm(r_l, r_b):
            actions = ["return_confirm"]
    return actions
