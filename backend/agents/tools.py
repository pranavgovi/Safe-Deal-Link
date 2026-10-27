"""Tool functions used by the agents. Each wraps either the database or the
PayPal client so agent modules never touch SQLAlchemy sessions or PayPal
HTTP calls directly. Named to match the Tools column in the build guide."""

from datetime import datetime

from agents.llm import call_json_vision
from db.models import Decision, Deal, Event
from db.session import SessionLocal
from paypal import client as paypal
from services import state
from storage import local_path_for_url


def get_listing(deal_id: str) -> dict:
    db = SessionLocal()
    try:
        deal = db.get(Deal, deal_id)
        if not deal:
            raise ValueError(f"No deal {deal_id}")
        return {
            "id": deal.id,
            "title": deal.title,
            "description": deal.description,
            "price": deal.price,
            "photo_urls": deal.photo_urls or [],
            "seller_email": deal.seller_email,
            "status": deal.status,
        }
    finally:
        db.close()


def estimate_market_price(title: str, description: str) -> dict:
    """No external pricing API is wired up. This tells the listing guard
    that no independent price signal is available, so it should reason
    from the listing text (vague description, urgency language, price vs.
    typical resale categories) instead of a real comp."""
    return {"estimated_price": None, "note": "market price lookup not configured"}


def flag_risk(deal_id: str, score: float, reasons: list):
    db = SessionLocal()
    try:
        deal = db.get(Deal, deal_id)
        deal.risk_score = score
        deal.risk_reasons = reasons
        db.commit()
    finally:
        db.close()


def get_tracking_status(deal_id: str) -> dict:
    db = SessionLocal()
    try:
        deal = db.get(Deal, deal_id)
        return {
            "carrier": deal.carrier,
            "tracking_number": deal.tracking_number,
            "status": deal.status,
        }
    finally:
        db.close()


def compare_photo_to_listing(deal_id: str) -> dict:
    """Vision comparison of the buyer's uploaded photo against the listing.
    Returns {"match": bool, "confidence": float, "reasoning": str}."""
    db = SessionLocal()
    try:
        deal = db.get(Deal, deal_id)
        if not deal.buyer_photo_url:
            raise ValueError("No buyer photo uploaded yet")
        photo_path = local_path_for_url(deal.buyer_photo_url)
        listing = {
            "title": deal.title,
            "description": deal.description,
            "price": deal.price,
        }
    finally:
        db.close()

    with open(photo_path, "rb") as f:
        image_bytes = f.read()

    system = (
        "You are the Verifier agent for an escrow marketplace. You compare a "
        "photo the buyer uploaded against the seller's listing. Respond with "
        'ONLY a JSON object: {"match": bool, "confidence": 0-1 float, '
        '"reasoning": short string}. match=true only if the photographed '
        "item plausibly is the listed item in roughly the condition described."
    )
    prompt = (
        f"Listing title: {listing['title']}\n"
        f"Listing description: {listing['description']}\n"
        f"Listed price: {listing['price']}\n\n"
        "The attached photo is what the buyer says they received. Does it match?"
    )
    return call_json_vision(system, prompt, image_bytes)


def ask_party(deal_id: str, message: str):
    """No live messaging channel exists yet — this logs an event visible on
    the deal timeline so a human reviewer sees the open question."""
    log_event(deal_id, "scheduler", "agent_question", {"message": message})


def log_decision(deal_id: str, agent: str, action: str, reasoning: str, confidence: float = None, inputs: dict = None):
    db = SessionLocal()
    try:
        decision = Decision(
            deal_id=deal_id,
            agent=agent,
            action=action,
            reasoning=reasoning,
            confidence=confidence,
            inputs=inputs or {},
        )
        db.add(decision)
        db.commit()
    finally:
        db.close()


def log_event(deal_id: str, source: str, type_: str, payload: dict = None):
    db = SessionLocal()
    try:
        event = Event(deal_id=deal_id, source=source, type=type_, payload=payload or {})
        db.add(event)
        db.commit()
    finally:
        db.close()


def move_deal(deal_id: str, target_status: str):
    db = SessionLocal()
    try:
        deal = db.get(Deal, deal_id)
        state.transition(deal, target_status)
        db.commit()
    finally:
        db.close()


def create_order(deal_id: str) -> dict:
    db = SessionLocal()
    try:
        deal = db.get(Deal, deal_id)
        order = paypal.create_order(deal.price, deal.seller_email, deal.id)
        deal.order_id = order["id"]
        db.commit()
        return order
    finally:
        db.close()


def get_authorization(auth_id: str) -> dict:
    return paypal.get_authorization(auth_id)


def reauthorize(deal_id: str) -> dict:
    """Refreshes the 3-day honor window. Does NOT touch auth_expires_at —
    PayPal's 29-day hard cap is fixed from the original authorization and
    reauthorizing cannot extend it."""
    db = SessionLocal()
    try:
        deal = db.get(Deal, deal_id)
        result = paypal.reauthorize(deal.authorization_id, deal.price)
        deal.authorized_at = datetime.utcnow()
        db.commit()
        return result
    finally:
        db.close()


def void_authorization(deal_id: str):
    db = SessionLocal()
    try:
        deal = db.get(Deal, deal_id)
        paypal.void_authorization(deal.authorization_id)
        state.transition(deal, state.VOIDED)
        db.commit()
    finally:
        db.close()


def capture(deal_id: str, amount: float, final: bool = True) -> dict:
    db = SessionLocal()
    try:
        deal = db.get(Deal, deal_id)
        result = paypal.capture_authorization(deal.authorization_id, amount, deal.id, final=final)
        deal.capture_id = result["id"]
        state.transition(deal, state.CAPTURED)
        db.commit()
        return result
    finally:
        db.close()


def void(deal_id: str):
    void_authorization(deal_id)


def escalate_to_human(deal_id: str, reason: str):
    db = SessionLocal()
    try:
        deal = db.get(Deal, deal_id)
        state.transition(deal, state.NEEDS_HUMAN)
        db.commit()
    finally:
        db.close()
    log_event(deal_id, "scheduler", "escalated", {"reason": reason})
