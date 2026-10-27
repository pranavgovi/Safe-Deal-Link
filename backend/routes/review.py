"""Human review queue: deals escalated to NEEDS_HUMAN, and the human
decision that resolves them (capture, partial capture, or void)."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents import tools
from db.models import Deal
from db.session import get_db
from routes.deals import serialize_deal
from services import state

router = APIRouter(prefix="/review", tags=["review"])


class ReviewDecisionRequest(BaseModel):
    decision: str  # "capture" | "partial" | "void"
    amount: Optional[float] = None  # required for "partial"


@router.get("")
def list_review_queue(db: Session = Depends(get_db)):
    deals = (
        db.query(Deal).filter(Deal.status == state.NEEDS_HUMAN).order_by(Deal.created_at).all()
    )
    return [serialize_deal(d) for d in deals]


@router.post("/{deal_id}")
def resolve_deal(deal_id: str, body: ReviewDecisionRequest, db: Session = Depends(get_db)):
    deal = db.get(Deal, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if deal.status != state.NEEDS_HUMAN:
        raise HTTPException(status_code=409, detail=f"Deal is {deal.status}, expected NEEDS_HUMAN")

    if body.decision == "void":
        tools.void_authorization(deal_id)
        tools.log_decision(deal_id, agent="human", action="void", reasoning="resolved by human reviewer")
    elif body.decision in ("capture", "partial"):
        amount = body.amount if body.decision == "partial" else deal.price
        if amount is None or amount <= 0 or amount > deal.price:
            raise HTTPException(status_code=400, detail="Invalid capture amount")
        tools.capture(deal_id, amount, final=True)
        tools.log_decision(
            deal_id,
            agent="human",
            action=body.decision,
            reasoning="resolved by human reviewer",
            inputs={"amount": amount},
        )
    else:
        raise HTTPException(status_code=400, detail="decision must be capture, partial, or void")

    db.refresh(deal)
    return serialize_deal(deal)
