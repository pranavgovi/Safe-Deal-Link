"""Checks tracking and compares the buyer's photo to the listing. Read
only — never moves money. The Resolver acts on this agent's output."""

from agents import tools


def verify(deal_id: str) -> dict:
    tracking = tools.get_tracking_status(deal_id)

    try:
        comparison = tools.compare_photo_to_listing(deal_id)
        match = bool(comparison.get("match"))
        confidence = float(comparison.get("confidence", 0.0))
        reasoning = comparison.get("reasoning", "")
    except Exception as exc:
        # No photo, a broken/missing LLM key, or a bad JSON parse — treat
        # as "no match" so the Resolver's guardrails route this to a human
        # instead of silently proceeding on bad data.
        match = False
        confidence = 0.0
        reasoning = f"verifier error: {exc}"

    tools.log_decision(
        deal_id,
        agent="verifier",
        action="match" if match else "no_match",
        reasoning=reasoning,
        confidence=confidence,
        inputs={"tracking": tracking},
    )

    return {"match": match, "confidence": confidence, "reasoning": reasoning}
