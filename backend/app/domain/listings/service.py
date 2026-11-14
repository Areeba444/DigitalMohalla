"""ListingService: create, edit, draft, publish and pause a listing (Module 3, FR-B-01, UC-B1).

Any approved member of a community can lend: a listing belongs to its owner and to one of the
owner's communities, and a person is a lender only on the loans of items they own (roles are per
loan, never per account). Publishing needs a description and a condition (DA-23); the database
checks the same with `item_published_complete_ck`, so a client cannot skip it.

Status moves an owner may make (others are a moderator's, e.g. REMOVED, or the scheduler's, EXPIRED):

    DRAFT -> DRAFT (edit), DRAFT -> PUBLISHED, PUBLISHED <-> PAUSED, EXPIRED -> PUBLISHED

A saved listing is re-embedded for meaning-based search (A9) through `on_saved`; until A9 is built,
keyword search reads the generated `search_tsv` column and needs nothing here.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from app.domain.lifecycle.errors import InvalidTransition, NotAuthorised, StreamNotFound

CONDITIONS = ("NEW", "GOOD", "FAIR", "WORN")
VALUE_BANDS = ("LOW", "MEDIUM", "HIGH")
OWNER_MOVES = {
    ("DRAFT", "DRAFT"),
    ("DRAFT", "PUBLISHED"),
    ("PUBLISHED", "PUBLISHED"),
    ("PUBLISHED", "PAUSED"),
    ("PAUSED", "PAUSED"),
    ("PAUSED", "PUBLISHED"),
    ("EXPIRED", "PUBLISHED"),
}
EDITABLE = (
    "title",
    "description",
    "category_id",
    "condition",
    "value_band",
    "deposit_amount",
    "usage_terms",
    "handover_method",
    "search_terms",
    "expires_at",
)
LIMITS = {"title": 120, "usage_terms": 2000, "handover_method": 200, "search_terms": 300}


class InvalidListing(ValueError):
    """The listing cannot be saved as asked (422), e.g. publishing without a description."""


@dataclass(frozen=True)
class ListingDraft:
    """Fields of a listing; None means "not given" on an edit."""

    title: str | None = None
    description: str | None = None
    category_id: int | None = None
    condition: str | None = None
    value_band: str | None = None
    deposit_amount: float | None = None
    usage_terms: str | None = None
    handover_method: str | None = None
    search_terms: str | None = None
    expires_at: datetime | None = None


class ListingStore(Protocol):
    def is_approved_member(self, user_id: UUID, community_id: UUID) -> bool: ...

    def category(self, category_id: int) -> dict[str, Any] | None: ...

    def insert(
        self, owner_id: UUID, community_id: UUID, status: str, fields: Mapping[str, Any]
    ) -> UUID: ...

    def listing(self, item_id: UUID) -> dict[str, Any] | None: ...

    def update(self, item_id: UUID, status: str, fields: Mapping[str, Any]) -> None: ...


def _clean(draft: ListingDraft) -> dict[str, Any]:
    """Given fields only, trimmed and checked; empty optional text becomes None."""
    out: dict[str, Any] = {}
    for name in EDITABLE:
        value = getattr(draft, name)
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
            if name in LIMITS and len(value) > LIMITS[name]:
                raise InvalidListing(f"{name} is longer than {LIMITS[name]} characters")
            if not value and name == "title":
                raise InvalidListing("a listing needs a title")
            value = value or None
        out[name] = value
    if out.get("condition") not in (None, *CONDITIONS):
        raise InvalidListing(f"condition must be one of {', '.join(CONDITIONS)}")
    if out.get("value_band") not in (None, *VALUE_BANDS):
        raise InvalidListing(f"value_band must be one of {', '.join(VALUE_BANDS)}")
    if out.get("deposit_amount") is not None and out["deposit_amount"] < 0:
        raise InvalidListing("the deposit cannot be negative")
    return out


class ListingService:
    def __init__(
        self,
        store: ListingStore,
        *,
        now: datetime,
        default_expiry_days: float | None = None,
        on_saved: Callable[[UUID], None] | None = None,
    ) -> None:
        self.store = store
        self.now = now
        self.default_expiry_days = default_expiry_days
        self.on_saved = on_saved or (lambda _item: None)

    def create(
        self, owner_id: UUID, community_id: UUID, draft: ListingDraft, *, publish: bool
    ) -> dict[str, Any]:
        if not self.store.is_approved_member(owner_id, community_id):
            raise NotAuthorised("only an approved member of this community can list an item here")
        fields = _clean(draft)
        for required in ("title", "category_id", "value_band"):
            if fields.get(required) is None:
                raise InvalidListing(f"a listing needs {required.replace('_', ' ')}")
        fields["required_verification"] = self._category(fields["category_id"])["min_verification"]
        status = "PUBLISHED" if publish else "DRAFT"
        if publish:
            self._default_end(fields, None)
            self._ready_to_publish(fields)
        item_id = self.store.insert(owner_id, community_id, status, fields)
        self.on_saved(item_id)
        return self._get(item_id)

    def update(
        self, owner_id: UUID, item_id: UUID, draft: ListingDraft, status: str | None
    ) -> dict[str, Any]:
        current = self._get(item_id)
        if current["owner_id"] != owner_id:
            raise NotAuthorised("only the owner can edit this listing")
        target = status or current["status"]
        if (current["status"], target) not in OWNER_MOVES:
            raise InvalidTransition(
                f"a listing that is {current['status'].lower()} cannot be made {target.lower()}"
            )
        fields = _clean(draft)
        if "category_id" in fields:
            category = self._category(fields["category_id"])
            fields["required_verification"] = category["min_verification"]
        if target == "PUBLISHED":
            self._default_end(fields, current.get("expires_at"))
            self._ready_to_publish({**current, **fields})
        self.store.update(item_id, target, fields)
        self.on_saved(item_id)
        return self._get(item_id)

    def get(self, viewer_id: UUID, item_id: UUID) -> dict[str, Any]:
        """Published listings are visible to members; drafts and paused ones only to the owner."""
        item = self._get(item_id)
        if item["status"] != "PUBLISHED" and item["owner_id"] != viewer_id:
            raise StreamNotFound(f"item {item_id}")
        return item

    # ------------------------------------------------------------------ helpers
    def _ready_to_publish(self, fields: Mapping[str, Any]) -> None:
        missing = [n for n in ("description", "condition") if not fields.get(n)]
        if missing:
            raise InvalidListing(f"add {' and '.join(missing)} before publishing (FR-B-01)")
        expires = fields.get("expires_at")
        if expires is not None and expires <= self.now:
            raise InvalidListing("the listing end date must be in the future")

    def _default_end(self, fields: dict[str, Any], current_end: datetime | None) -> None:
        """Publishing without a (future) end date sets one `listing_default_expiry_days` ahead, so
        the listing-expiry job (ADR-0012) only ever reads `expires_at`."""
        if "expires_at" in fields or self.default_expiry_days is None:
            return
        if current_end is None or current_end <= self.now:
            fields["expires_at"] = self.now + timedelta(days=self.default_expiry_days)

    def _category(self, category_id: int) -> dict[str, Any]:
        category = self.store.category(category_id)
        if category is None:
            raise InvalidListing("unknown category")
        return category

    def _get(self, item_id: UUID) -> dict[str, Any]:
        item = self.store.listing(item_id)
        if item is None:
            raise StreamNotFound(f"item {item_id}")
        return item
