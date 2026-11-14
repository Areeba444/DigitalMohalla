"""AttachmentService: listing photos and handover, return and dispute photos (M4, ADR-0014).

Who may upload: the owner, for a listing; a party to the loan, for a loan. A handover or return
photo belongs to that party's own latest condition report of the phase (record the checklist
first); a dispute photo belongs to the loan while it is disputed. Every file passes the checks of
`policy.check_and_strip` before it reaches storage, and the database row records its SHA-256 for
tamper evidence and `metadata_stripped = true` (the schema refuses anything else).

Who may see: a listing photo, any approved member of the listing's community and the owner; a loan
photo, the two parties, a moderator of the community, or an admin. They receive a short-lived signed
URL, never a public link (ADR-0014).
"""

import hashlib
from typing import Any, Protocol
from uuid import UUID

from app.domain.lifecycle.errors import InvalidTransition, NotAuthorised, StreamNotFound
from app.domain.uploads.policy import check_and_strip
from app.domain.uploads.storage import StoragePort

PHASE_STATES = {
    "HANDOVER": {"ACCEPTED", "ACTIVE"},
    "RETURN": {"RETURN_INITIATED", "RETURNED", "COMPLETED"},
    "DISPUTE": {"DISPUTED"},
}


class AttachmentStore(Protocol):
    def item(self, item_id: UUID) -> dict[str, Any] | None: ...

    def loan(self, txn_id: UUID) -> dict[str, Any] | None: ...

    def latest_report(self, txn_id: UUID, phase: str, role: str) -> UUID | None: ...

    def insert(
        self,
        *,
        uploaded_by: UUID,
        key: str,
        sha256: bytes,
        mime: str,
        item_id: UUID | None = None,
        transaction_id: UUID | None = None,
        condition_report_id: UUID | None = None,
    ) -> UUID: ...

    def attachment(self, attachment_id: UUID) -> dict[str, Any] | None: ...

    def is_member(self, user_id: UUID, community_id: UUID) -> bool: ...

    def is_moderator(self, user_id: UUID, community_id: UUID) -> bool: ...


class AttachmentService:
    def __init__(
        self, store: AttachmentStore, storage: StoragePort, *, max_bytes: int, url_ttl_seconds: int
    ) -> None:
        self.store = store
        self.storage = storage
        self.max_bytes = max_bytes
        self.ttl = url_ttl_seconds

    def add_item_photo(self, actor_id: UUID, item_id: UUID, data: bytes) -> dict[str, Any]:
        item = self.store.item(item_id)
        if item is None:
            raise StreamNotFound(f"item {item_id}")
        if item["owner_id"] != actor_id:
            raise NotAuthorised("only the owner can add photos to this listing")
        return self._save(actor_id, data, item_id=item_id)

    def add_loan_photo(
        self, actor_id: UUID, txn_id: UUID, purpose: str, data: bytes
    ) -> dict[str, Any]:
        loan = self.store.loan(txn_id)
        if loan is None:
            raise StreamNotFound(f"transaction {txn_id}")
        role = {loan["borrower_id"]: "BORROWER", loan["lender_id"]: "LENDER"}.get(actor_id)
        if role is None:
            raise NotAuthorised("only the borrower or the lender of this loan can add photos")
        if loan["state"] not in PHASE_STATES[purpose]:
            raise InvalidTransition(f"{purpose.lower()} photos are not taken while {loan['state']}")
        report_id = None
        if purpose in ("HANDOVER", "RETURN"):
            report_id = self.store.latest_report(txn_id, purpose, role)
            if report_id is None:
                raise InvalidTransition(f"record your {purpose.lower()} checklist first")
        return self._save(actor_id, data, transaction_id=txn_id, condition_report_id=report_id)

    def url(self, actor_id: UUID, platform_role: str, attachment_id: UUID) -> tuple[str, int]:
        a = self.store.attachment(attachment_id)
        if a is None:
            raise StreamNotFound(f"attachment {attachment_id}")
        if not self._may_view(actor_id, platform_role, a):
            raise NotAuthorised("you cannot see this photo")
        return self.storage.signed_url(a["storage_key"], self.ttl)

    # ------------------------------------------------------------------ helpers
    def _save(self, actor_id: UUID, data: bytes, **target: UUID | None) -> dict[str, Any]:
        clean = check_and_strip(data, self.max_bytes)  # 422 before anything is stored
        key = self.storage.put(clean.data, clean.mime)  # 503 when storage is unavailable
        attachment_id = self.store.insert(
            uploaded_by=actor_id,
            key=key,
            sha256=hashlib.sha256(clean.data).digest(),
            mime=clean.mime,
            **target,
        )
        url, exp = self.storage.signed_url(key, self.ttl)
        return {"id": attachment_id, "url": url, "expires_at": exp, "mime_type": clean.mime}

    def _may_view(self, actor_id: UUID, platform_role: str, a: dict[str, Any]) -> bool:
        if platform_role == "ADMIN":
            return True
        if a["item_id"] is not None:
            return a["owner_id"] == actor_id or self.store.is_member(actor_id, a["community_id"])
        return actor_id in (a["borrower_id"], a["lender_id"]) or self.store.is_moderator(
            actor_id, a["community_id"]
        )
