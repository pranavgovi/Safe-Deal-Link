"""Decides capture, partial capture, void, or escalate. The only agent
allowed to move money — every action is checked against guardrails.py
before it ever reaches PayPal."""

from agents import tools
from agents.guardrails import GuardrailViolation, check_capture
from db.models import Deal
from db.session import SessionLocal


def decide(deal_id: str, verifier_result: dict) -> dict:
    db = SessionLocal()
    try:
        deal = db.get(Deal, deal_id)
        amount = deal.price
    finally:
        db.close()

    try:
        check_capture(deal, verifier_result, amount)
    except GuardrailViolation as violation:
        tools.escalate_to_human(deal_id, violation.reason)
        tools.log_decision(
            deal_id,
            agent="resolver",
            action="escalate",
            reasoning=violation.reason,
            confidence=verifier_result.get("confidence"),
            inputs={"verifier_result": verifier_result},
        )
        return {"action": "escalate", "reason": violation.reason}

    result = tools.capture(deal_id, amount, final=True)
    tools.log_decision(
        deal_id,
        agent="resolver",
        action="capture",
        reasoning="verifier matched above confidence threshold; guardrails passed",
        confidence=verifier_result.get("confidence"),
        inputs={"verifier_result": verifier_result, "capture_id": result.get("id")},
    )
    return {"action": "capture", "capture_id": result.get("id")}
