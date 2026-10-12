"""Slice A stand-in for the assurance engine (IAssess).

Always answers INSUFFICIENT_EVIDENCE through rule R3 (no verified history), exactly as the plan's
Slice A says. It exists so the lifecycle loop can run end to end before the real engine (Slice B,
Student 2) replaces it behind the same interface. It is NOT an assessment of anyone.
"""

from app.domain.lifecycle.ports import AssessmentRequest, AssessmentResult


class StubAssuranceEngine:
    def assess(self, request: AssessmentRequest) -> AssessmentResult:
        return AssessmentResult(
            assurance_state="INSUFFICIENT_EVIDENCE",
            policy_decision="REQUEST_VERIFICATION",
            rule_fired="R3",
            hold_reason=None,
            explanation=(
                "Insufficient verified history; lender review required. "
                "This is not a negative finding about the borrower. "
                "(Placeholder engine: the real assessment arrives in Slice B.)"
            ),
            config_version=request.config_version,
            posterior_mean=0.5,
            ci90_low=0.05,
            ci90_high=0.95,
            effective_evidence=0.0,
            safeguards=[  # policy output for a newcomer (Overview 5.8): deposit record, photos, fixed return
                {"code": "DEPOSIT_RECORD", "label": "Record the deposit before handover"},
                {"code": "HANDOVER_PHOTOS", "label": "Take item photos at handover"},
                {"code": "FIXED_RETURN_DATE", "label": "Agree a fixed return date"},
            ],
        )
