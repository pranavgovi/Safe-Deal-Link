"""Watches the hold, renews or voids before the 29-day PayPal authorization
expiry. Runs on a schedule (see backend/scheduler.py) — it never fires from
a live request, only from polling the DB for deals it needs to act on.

Two independent clocks matter here:
  - the 3-day "honor" window (authorized_at + 3d): PayPal only *guarantees*
    a capture will succeed within this window; reauthorizing refreshes it.
  - the 29-day hard cap (auth_expires_at): fixed from the ORIGINAL
    authorization and never extended, even by reauthorizing.
"""

from datetime import datetime, timedelta

from agents import tools
from db.models import Deal
from db.session import SessionLocal
from services import state

HONOR_PERIOD = timedelta(days=3)
REAUTH_BUFFER = timedelta(hours=6)  # reauthorize a bit before the honor window lapses
VOID_BUFFER = timedelta(days=1)  # void with a day of margin before the hard 29-day expiry

WATCHED_STATES = {state.AUTHORIZED, state.SHIPPED, state.DELIVERED, state.VERIFYING}


def run_escrow_checks():
    db = SessionLocal()
    try:
        deals = db.query(Deal).filter(Deal.status.in_(WATCHED_STATES)).all()
        deal_ids = [d.id for d in deals]
    finally:
        db.close()

    for deal_id in deal_ids:
        _check_deal(deal_id)


def _check_deal(deal_id: str):
    db = SessionLocal()
    try:
        deal = db.get(Deal, deal_id)
        if not deal or not deal.auth_expires_at or not deal.authorized_at:
            return
        auth_expires_at = deal.auth_expires_at
        honor_boundary = deal.authorized_at + HONOR_PERIOD
    finally:
        db.close()

    now = datetime.utcnow()

    if auth_expires_at - now <= VOID_BUFFER:
        tools.void_authorization(deal_id)
        tools.log_decision(
            deal_id,
            agent="escrow",
            action="void",
            reasoning="authorization was about to hit its 29-day hard expiry before the deal resolved",
        )
        return

    if honor_boundary - now <= REAUTH_BUFFER:
        tools.reauthorize(deal_id)
        tools.log_decision(
            deal_id,
            agent="escrow",
            action="reauthorize",
            reasoning="renewed the 3-day honor window before it lapsed",
        )
