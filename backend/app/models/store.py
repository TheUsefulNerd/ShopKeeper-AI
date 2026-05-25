import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DECIMAL, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.user_id"),
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    balance: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 2),
        nullable=False,
        default=Decimal("40000.00"),
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
