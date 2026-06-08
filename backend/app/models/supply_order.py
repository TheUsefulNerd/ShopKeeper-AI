import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DECIMAL, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SupplyOrderStatus(enum.Enum):
    pending = "pending"
    delivered = "delivered"


class SupplyOrder(Base):
    __tablename__ = "supply_orders"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    supply_recommendation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("supply_recommendations.id"),
        nullable=False,
    )
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id"),
        nullable=False,
    )
    quantity_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    cost: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    status: Mapped[SupplyOrderStatus] = mapped_column(
        SAEnum(SupplyOrderStatus, native_enum=False),
        nullable=False,
        default=SupplyOrderStatus.pending,
    )
    expected_delivery_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
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
