"""Money rules checked before any PayPal call. Every rule must pass for the
Resolver to capture; any failure sends the deal to NEEDS_HUMAN instead."""

from datetime import datetime

from db.models import Deal
from services import state

CONFIDENCE_THRESHOLD = 0.85


class GuardrailViolation(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def check_capture(deal: Deal, verifier_result: dict, requested_amount: float):
    """Raises GuardrailViolation with a human-readable reason if any of the
    five capture rules fails. Returns silently if capture may proceed."""

    if deal.status != state.VERIFYING:
        raise GuardrailViolation(f"deal is in {deal.status}, not VERIFYING")

    if not verifier_result.get("match"):
        raise GuardrailViolation("verifier did not find a match")

    confidence = verifier_result.get("confidence", 0)
    if confidence < CONFIDENCE_THRESHOLD:
        raise GuardrailViolation(
            f"verifier confidence {confidence} below threshold {CONFIDENCE_THRESHOLD}"
        )

    if requested_amount > deal.price:
        raise GuardrailViolation(
            f"requested amount {requested_amount} exceeds authorized amount {deal.price}"
        )

    if deal.auth_expires_at and deal.auth_expires_at < datetime.utcnow():
        raise GuardrailViolation("authorization has expired")

    if deal.capture_id:
        raise GuardrailViolation("deal has already been captured")
