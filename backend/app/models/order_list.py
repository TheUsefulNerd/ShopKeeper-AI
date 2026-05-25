import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DECIMAL, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class OrderList(Base):
    """Junction table linking orders to products. Append-only — no updated_at."""

    __tablename__ = "order_list"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("orders.id"),
        nullable=False,
    )
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), nullable=False
    )  # snapshot of price at time of order
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
