#defines the models for deal ,events , decisions
import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import relationship

from db.session import Base


def gen_uuid():
    return str(uuid.uuid4())


class Deal(Base):
    __tablename__ = "deals"

    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    photo_urls = Column(JSON, default=list) #this is not assigned as [] because it will create shallow copies
    seller_email = Column(String, nullable=False)
    status = Column(String, nullable=False, default="CREATED")
    risk_score = Column(Float, nullable=True)
    risk_reasons = Column(JSON, default=list)
    order_id = Column(String, nullable=True)
    authorization_id = Column(String, nullable=True)
    capture_id = Column(String, nullable=True)
    authorized_at = Column(DateTime, nullable=True)
    auth_expires_at = Column(DateTime, nullable=True)
    carrier = Column(String, nullable=True)
    tracking_number = Column(String, nullable=True)
    buyer_photo_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    decisions = relationship(
        "Decision", back_populates="deal", cascade="all, delete-orphan"
    )
    events = relationship(
        "Event", back_populates="deal", cascade="all, delete-orphan"
    )


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(String, primary_key=True, default=gen_uuid)
    deal_id = Column(String, ForeignKey("deals.id"), nullable=False)
    agent = Column(String, nullable=False)
    action = Column(String, nullable=False)
    reasoning = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    inputs = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    deal = relationship("Deal", back_populates="decisions")


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=gen_uuid)
    deal_id = Column(String, ForeignKey("deals.id"), nullable=False)
    source = Column(String, nullable=False)  # user, webhook, scheduler
    type = Column(String, nullable=False)
    payload = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    deal = relationship("Deal", back_populates="events")
