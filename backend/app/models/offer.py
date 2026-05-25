import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DECIMAL, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Offer(Base):
    __tablename__ = "offers"

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
        nullable=True,  # null = not yet redeemed
    )
    code: Mapped[str] = mapped_column(String(255), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False)
    is_redeemed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
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
