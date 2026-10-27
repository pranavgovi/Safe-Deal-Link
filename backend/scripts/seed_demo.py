"""Seeds a few ready-made deals at different lifecycle stages so a demo
doesn't have to wait on real PayPal/LLM round-trips to show the UI off.

These use fabricated PayPal IDs (order_id/authorization_id) — fine for
showing the timeline, risk badge, and review queue, but don't try to
actually capture/void them; there's no real authorization behind them.

Run from backend/ (venv active): python -m scripts.seed_demo
"""

from datetime import datetime, timedelta

from db.models import Decision, Deal, Event
from db.session import SessionLocal
from services import state


def main():
    db = SessionLocal()
    try:
        ready_to_pay = Deal(
            title="Trek mountain bike, size M",
            description="2 years old, well maintained, new tires last month.",
            price=350.0,
            seller_email="seller@example.com",
            status=state.SCREENED,
            risk_score=0.1,
            risk_reasons=["Price in line with similar listings"],
        )
        db.add(ready_to_pay)

        shipped = Deal(
            title="PS5 console, disc edition",
            description="Barely used, includes one controller and all cables.",
            price=380.0,
            seller_email="seller@example.com",
            status=state.AUTHORIZED,
            risk_score=0.15,
            risk_reasons=[],
            order_id="DEMO-ORDER-1",
            authorization_id="DEMO-AUTH-1",
            authorized_at=datetime.utcnow(),
            auth_expires_at=datetime.utcnow() + timedelta(days=29),
        )
        db.add(shipped)

        needs_review = Deal(
            title="Herman Miller Aeron chair, size B",
            description="Great condition, no rips, fully adjustable.",
            price=420.0,
            seller_email="seller@example.com",
            status=state.NEEDS_HUMAN,
            risk_score=0.2,
            risk_reasons=[],
            order_id="DEMO-ORDER-2",
            authorization_id="DEMO-AUTH-2",
            authorized_at=datetime.utcnow() - timedelta(days=5),
            auth_expires_at=datetime.utcnow() + timedelta(days=24),
            carrier="UPS",
            tracking_number="1Z999AA10123456784",
            buyer_photo_url="/uploads/demo-received-chair.jpg",
        )
        db.add(needs_review)

        db.commit()
        db.refresh(ready_to_pay)
        db.refresh(shipped)
        db.refresh(needs_review)

        db.add(Event(deal_id=ready_to_pay.id, source="user", type="deal_created", payload={}))
        db.add(
            Decision(
                deal_id=ready_to_pay.id,
                agent="listing_guard",
                action="score",
                reasoning="Price and description are consistent with a typical resale listing.",
                confidence=0.1,
            )
        )

        db.add(Event(deal_id=shipped.id, source="user", type="authorized", payload={}))
        db.add(
            Decision(
                deal_id=shipped.id,
                agent="listing_guard",
                action="score",
                reasoning="No scam indicators found.",
                confidence=0.15,
            )
        )

        db.add(Event(deal_id=needs_review.id, source="user", type="photo_uploaded", payload={}))
        db.add(
            Decision(
                deal_id=needs_review.id,
                agent="verifier",
                action="no_match",
                reasoning="Listing shows a black Aeron chair; photo shows a grey one — possible wrong item shipped.",
                confidence=0.55,
            )
        )
        db.add(
            Decision(
                deal_id=needs_review.id,
                agent="resolver",
                action="escalate",
                reasoning="verifier confidence 0.55 below threshold 0.85",
                confidence=0.55,
            )
        )
        db.commit()

        print("Seeded demo deals:")
        print(f"  Ready to pay:  /deal/{ready_to_pay.id}")
        print(f"  Authorized:    /deal/{shipped.id}/timeline")
        print(f"  Needs review:  /deal/{needs_review.id}/timeline  (also appears on /review)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
