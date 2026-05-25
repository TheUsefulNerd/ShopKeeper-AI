import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id"),
        unique=True,
        nullable=False,
    )
    quantity_available: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    quantity_reserved: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    low_stock_threshold: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5
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
