"""Request and response models of the REST API (Architecture_Design.md section 4).

Responses carry ids, states and evidence only. No address, coordinates or CNIC field exists in any
model (NFR-PR-01, NFR-S-07), and an assurance state is always returned with its evidence and
explanation, never as a single trust number (NFR-U-01).
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RequestIn(BaseModel):
    item_id: UUID
    start_date: date
    end_date: date = Field(description="Exclusive end: the item is returned by this date")
    message: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _dates_in_order(self) -> "RequestIn":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

    def period(self) -> str:
        return f"[{self.start_date}T00:00:00+00,{self.end_date}T00:00:00+00)"


class DeclineIn(BaseModel):
    reason: str | None = Field(default=None, max_length=200)


class ChecklistIn(BaseModel):
    checklist: dict[str, Any] = Field(default_factory=dict)
    deposit_received: bool | None = None
    notes: str | None = Field(default=None, max_length=500)


class ConfirmIn(BaseModel):
    condition_agreed: bool = True
    checklist: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = Field(default=None, max_length=500)


class CommandOut(BaseModel):
    transaction_id: UUID
    state: str | None
    message: str | None = None
    hold_reason: str | None = None


class AssessmentOut(BaseModel):
    assurance_state: str
    policy_decision: str
    rule_fired: str
    config_version: str
    explanation: str
    safeguards: list[Any]
    posterior_mean: float | None = None
    ci90_low: float | None = None
    ci90_high: float | None = None
    effective_evidence: float | None = None
    # risk is a separate dimension and is never averaged with reliability (FR-T-05, NFR-U-01)
    manipulation_risk: int = 0
    manipulation_level: int = 1


class ReportOut(BaseModel):
    phase: str
    reporter_role: str
    condition_agreed: bool
    checklist: Any
    deposit_received: bool | None = None
    notes: str | None = None
    created_at: datetime


class RequestOut(BaseModel):
    transaction_id: UUID
    item_id: UUID
    item_title: str
    state: str | None
    hold_reason: str | None
    your_role: str | None
    borrower_name: str
    lender_name: str
    requested_period: str
    message: str | None
    deposit_required: bool
    assessment: AssessmentOut | None
    reports: list[ReportOut]
    available_actions: list[str]


class MyRequestOut(BaseModel):
    id: UUID
    item_id: UUID
    title: str
    state: str | None
    hold_reason: str | None
    requested_period: str
    your_role: str
    counterpart_name: str
    assurance_state: str | None


class BrowseItemOut(BaseModel):
    id: UUID
    title: str
    value_band: str
    deposit_amount: float
    owner_name: str


class EventOut(BaseModel):
    stream_seq: int
    event_type: str
    previous_state: str | None
    new_state: str
    occurred_at: datetime
    authorisation: str
    config_version: str | None = None


class LenderRequestOut(BaseModel):
    id: UUID
    item_id: UUID
    title: str
    state: str | None
    assurance_state: str | None
    requested_period: str


class ItemOut(BaseModel):
    id: UUID
    title: str
    value_band: str
    deposit_amount: float
    booked_periods: list[str]
