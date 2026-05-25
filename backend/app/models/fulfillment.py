import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FulfillmentType(enum.Enum):
    delivery = "delivery"
    pickup = "pickup"


class FulfillmentStatus(enum.Enum):
    pending = "pending"
    scheduled = "scheduled"
    completed = "completed"


class Fulfillment(Base):
    __tablename__ = "fulfillments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("orders.id"),
        unique=True,  # one fulfillment per order
        nullable=False,
    )
    type: Mapped[FulfillmentType] = mapped_column(
        SAEnum(FulfillmentType, native_enum=False),
        nullable=False,
    )
    status: Mapped[FulfillmentStatus] = mapped_column(
        SAEnum(FulfillmentStatus, native_enum=False),
        nullable=False,
        default=FulfillmentStatus.pending,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
