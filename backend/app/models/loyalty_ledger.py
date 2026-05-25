import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LoyaltyEventType(enum.Enum):
    earned = "earned"
    redeemed = "redeemed"


class LoyaltyLedger(Base):
    """Append-only ledger of loyalty point events. No updated_at."""

    __tablename__ = "loyalty_ledger"
    __table_args__ = (
        Index("ix_loyalty_ledger_customer_id_event_type", "customer_id", "event_type"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    customer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("customers.id"),
        nullable=False,
    )
    order_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("orders.id"),
        nullable=True,
    )
    event_type: Mapped[LoyaltyEventType] = mapped_column(
        SAEnum(LoyaltyEventType, native_enum=False),
        nullable=False,
    )
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
