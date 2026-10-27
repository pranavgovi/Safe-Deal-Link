"""Scores scam risk before payment. Can warn via risk_score/risk_reasons on
the deal, but per the guide it must never block payment by itself — the
deal always proceeds to SCREENED after this runs."""

from agents import tools
from agents.llm import call_json
from services import state

SYSTEM = (
    "You are the Listing Guard agent for a peer-to-peer escrow marketplace. "
    "You read a seller's listing and estimate the risk that it is a scam "
    "(fake item, price too good to be true, vague or stolen-sounding "
    "description, urgency pressure, mismatched price-to-description). "
    'Respond with ONLY a JSON object: {"risk_score": 0-1 float, "reasons": '
    "[short strings]}. risk_score near 0 means low risk, near 1 means high risk."
)


def score(deal_id: str) -> dict:
    listing = tools.get_listing(deal_id)
    market = tools.estimate_market_price(listing["title"], listing["description"])

    prompt = (
        f"Title: {listing['title']}\n"
        f"Description: {listing['description']}\n"
        f"Price: {listing['price']}\n"
        f"Market price signal: {market['note']}\n\n"
        "Assess scam risk."
    )

    try:
        result = call_json(SYSTEM, prompt)
        risk_score = float(result.get("risk_score", 0.0))
        reasons = result.get("reasons", [])
        reasoning = "; ".join(reasons) if reasons else "no concerns flagged"
    except Exception as exc:
        # Fail open: a broken/missing LLM key must never block a legitimate
        # deal — this agent can only ever warn, never block.
        risk_score = 0.0
        reasons = ["AI risk check unavailable"]
        reasoning = f"listing guard error: {exc}"

    tools.flag_risk(deal_id, risk_score, reasons)
    tools.log_decision(
        deal_id,
        agent="listing_guard",
        action="score",
        reasoning=reasoning,
        confidence=risk_score,
        inputs={"listing": listing},
    )
    tools.move_deal(deal_id, state.SCREENED)

    return {"risk_score": risk_score, "reasons": reasons}
