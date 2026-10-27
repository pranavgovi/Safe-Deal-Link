"""Deal lifecycle routes: create, view, pay, ship, deliver, upload photo,
timeline. See the build guide's Phase 4 route table."""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents import listing_guard
from agents.graph import run_verification_pipeline
from db.models import Decision, Deal, Event
from db.session import get_db
from paypal import client as paypal
from services import state
from storage import save_upload

router = APIRouter(prefix="/deals", tags=["deals"])

#this is the deal created by the seller to send it to buyer
class CreateDealRequest(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    photo_urls: List[str] = []
    seller_email: str


class TrackingRequest(BaseModel):
    carrier: str
    tracking_number: str


def serialize_deal(deal: Deal) -> dict:
    return {
        "id": deal.id,
        "title": deal.title,
        "description": deal.description,
        "price": deal.price,
        "photo_urls": deal.photo_urls or [],
        "seller_email": deal.seller_email,
        "status": deal.status,
        "risk_score": deal.risk_score,
        "risk_reasons": deal.risk_reasons or [],
        "order_id": deal.order_id,
        "authorization_id": deal.authorization_id,
        "capture_id": deal.capture_id,
        "auth_expires_at": deal.auth_expires_at.isoformat() if deal.auth_expires_at else None,
        "carrier": deal.carrier,
        "tracking_number": deal.tracking_number,
        "buyer_photo_url": deal.buyer_photo_url,
        "created_at": deal.created_at.isoformat() if deal.created_at else None,
    }


def get_deal_or_404(deal_id: str, db: Session) -> Deal:
    deal = db.get(Deal, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.post("")
def create_deal(body: CreateDealRequest, db: Session = Depends(get_db)):
    deal = Deal(
        title=body.title,
        description=body.description,
        price=body.price,
        photo_urls=body.photo_urls,
        seller_email=body.seller_email,
        status=state.CREATED,
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    deal_id = deal.id

    db.add(Event(deal_id=deal_id, source="user", type="deal_created", payload={}))
    db.commit()

    # Listing guard can warn but never block — the deal always proceeds to
    # SCREENED, even if the AI call itself fails (fails open, see
    # agents/listing_guard.py).
    listing_guard.score(deal_id)

    db.refresh(deal)
    return serialize_deal(deal)


@router.get("/{deal_id}")
def get_deal(deal_id: str, db: Session = Depends(get_db)):
    return serialize_deal(get_deal_or_404(deal_id, db))

#based on the deal, it creates a paypal order
@router.post("/{deal_id}/order")
def create_order(deal_id: str, db: Session = Depends(get_db)):
    deal = get_deal_or_404(deal_id, db)
    if deal.status != state.SCREENED:
        raise HTTPException(status_code=409, detail=f"Deal is {deal.status}, expected SCREENED")

    order = paypal.create_order(deal.price, deal.seller_email, deal.id)
    deal.order_id = order["id"]
    db.add(Event(deal_id=deal_id, source="user", type="order_created", payload={"order_id": order["id"]}))
    db.commit()
    return {"order_id": order["id"]}


@router.post("/{deal_id}/authorize")
def authorize_deal(deal_id: str, db: Session = Depends(get_db)):
    deal = get_deal_or_404(deal_id, db)
    if not deal.order_id:
        raise HTTPException(status_code=409, detail="No PayPal order on this deal yet")

    order = paypal.authorize_order(deal.order_id)
    try:
        authorization = order["purchase_units"][0]["payments"]["authorizations"][0]
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail="PayPal did not return an authorization")

    now = datetime.utcnow()
    deal.authorization_id = authorization["id"]
    deal.authorized_at = now
    deal.auth_expires_at = now + timedelta(days=29)
    state.transition(deal, state.AUTHORIZED)
    db.add(
        Event(
            deal_id=deal_id,
            source="user",
            type="authorized",
            payload={"authorization_id": authorization["id"]},
        )
    )
    db.commit()
    db.refresh(deal)
    return serialize_deal(deal)


@router.post("/{deal_id}/tracking")
def add_tracking(deal_id: str, body: TrackingRequest, db: Session = Depends(get_db)):
    deal = get_deal_or_404(deal_id, db)
    if deal.status != state.AUTHORIZED:
        raise HTTPException(status_code=409, detail=f"Deal is {deal.status}, expected AUTHORIZED")

    deal.carrier = body.carrier
    deal.tracking_number = body.tracking_number
    state.transition(deal, state.SHIPPED)
    db.add(
        Event(
            deal_id=deal_id,
            source="user",
            type="shipped",
            payload={"carrier": body.carrier, "tracking_number": body.tracking_number},
        )
    )
    db.commit()
    db.refresh(deal)
    return serialize_deal(deal)


@router.post("/{deal_id}/delivered")
def mark_delivered(deal_id: str, db: Session = Depends(get_db)):
    """Demo button to simulate delivery (no real carrier webhook wired up)."""
    deal = get_deal_or_404(deal_id, db)
    if deal.status != state.SHIPPED:
        raise HTTPException(status_code=409, detail=f"Deal is {deal.status}, expected SHIPPED")

    state.transition(deal, state.DELIVERED)
    db.add(Event(deal_id=deal_id, source="user", type="delivered", payload={}))
    db.commit()
    db.refresh(deal)
    return serialize_deal(deal)


@router.post("/{deal_id}/photo")
def upload_photo(deal_id: str, file: UploadFile, db: Session = Depends(get_db)):
    deal = get_deal_or_404(deal_id, db)
    if deal.status != state.DELIVERED:
        raise HTTPException(status_code=409, detail=f"Deal is {deal.status}, expected DELIVERED")

    url = save_upload(file)
    deal.buyer_photo_url = url
    state.transition(deal, state.VERIFYING)
    db.add(Event(deal_id=deal_id, source="user", type="photo_uploaded", payload={"url": url}))
    db.commit()

    # Runs Verifier -> Resolver synchronously so the response reflects the
    # final outcome (capture / void / escalate) for the demo.
    try:
        run_verification_pipeline(deal_id)
    except Exception as exc:
        db.add(
            Event(deal_id=deal_id, source="scheduler", type="pipeline_error", payload={"error": str(exc)})
        )
        db.commit()

    db.refresh(deal)
    return serialize_deal(deal)


@router.get("/{deal_id}/timeline")
def get_timeline(deal_id: str, db: Session = Depends(get_db)):
    get_deal_or_404(deal_id, db)
    decisions = (
        db.query(Decision).filter(Decision.deal_id == deal_id).order_by(Decision.created_at).all()
    )
    events = db.query(Event).filter(Event.deal_id == deal_id).order_by(Event.created_at).all()

    return {
        "decisions": [
            {
                "id": d.id,
                "agent": d.agent,
                "action": d.action,
                "reasoning": d.reasoning,
                "confidence": d.confidence,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in decisions
        ],
        "events": [
            {
                "id": e.id,
                "source": e.source,
                "type": e.type,
                "payload": e.payload,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
    }
