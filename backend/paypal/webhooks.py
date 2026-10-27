"""Webhook signature verification and event handling. Webhooks are the
source of truth for final payment status — the frontend/API flow updates
state optimistically, but a webhook confirms or corrects it."""

import requests

from agents import tools
from config import PAYPAL_BASE_URL, PAYPAL_WEBHOOK_ID
from db.models import Deal
from db.session import SessionLocal
from paypal.client import auth_headers
from services import state
from services.state import InvalidTransition


def verify_signature(headers: dict, body: dict) -> bool:
    """Calls PayPal's verify-webhook-signature endpoint. Returns True only
    if PayPal confirms the event is authentic and matches our webhook ID."""
    if not PAYPAL_WEBHOOK_ID:
        return False

    payload = {
        "auth_algo": headers.get("paypal-auth-algo"),
        "cert_url": headers.get("paypal-cert-url"),
        "transmission_id": headers.get("paypal-transmission-id"),
        "transmission_sig": headers.get("paypal-transmission-sig"),
        "transmission_time": headers.get("paypal-transmission-time"),
        "webhook_id": PAYPAL_WEBHOOK_ID,
        "webhook_event": body,
    }
    response = requests.post(
        f"{PAYPAL_BASE_URL}/v1/notifications/verify-webhook-signature",
        headers=auth_headers(),
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("verification_status") == "SUCCESS"


def _find_deal_by_authorization(db, auth_id: str):
    if not auth_id:
        return None
    return db.query(Deal).filter(Deal.authorization_id == auth_id).first()


def _safe_transition(deal_id: str, target: str):
    """Webhooks can arrive out of order relative to our own API-driven
    transitions (e.g. a capture webhook after we've already captured via
    the Resolver). Swallow InvalidTransition rather than 500ing — the
    state is already where it needs to be."""
    db = SessionLocal()
    try:
        deal = db.get(Deal, deal_id)
        if deal.status == target:
            return
        state.transition(deal, target)
        db.commit()
    except InvalidTransition:
        db.rollback()
    finally:
        db.close()


def handle_event(event: dict):
    event_type = event.get("event_type")
    resource = event.get("resource", {})

    db = SessionLocal()
    try:
        deal = None
        if event_type in ("PAYMENT.AUTHORIZATION.CREATED", "PAYMENT.AUTHORIZATION.VOIDED"):
            deal = _find_deal_by_authorization(db, resource.get("id"))
        elif event_type in (
            "PAYMENT.CAPTURE.COMPLETED",
            "PAYMENT.CAPTURE.PENDING",
            "PAYMENT.CAPTURE.DENIED",
        ):
            auth_id = (
                resource.get("supplementary_data", {})
                .get("related_ids", {})
                .get("authorization_id")
            )
            deal = _find_deal_by_authorization(db, auth_id)
        deal_id = deal.id if deal else None
    finally:
        db.close()

    if not deal_id:
        return  # Nothing in our DB matches this event; ignore.

    tools.log_event(deal_id, "webhook", event_type, resource)

    if event_type == "PAYMENT.AUTHORIZATION.VOIDED":
        _safe_transition(deal_id, state.VOIDED)

    elif event_type == "PAYMENT.CAPTURE.COMPLETED":
        db = SessionLocal()
        try:
            deal = db.get(Deal, deal_id)
            deal.capture_id = resource.get("id")
            db.commit()
        finally:
            db.close()
        _safe_transition(deal_id, state.CAPTURED)

    elif event_type == "PAYMENT.CAPTURE.DENIED":
        tools.escalate_to_human(deal_id, "PayPal denied the capture")
