import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DECIMAL, Boolean, DateTime, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ProductCategory(enum.Enum):
    groceries = "groceries"
    clothing = "clothing"
    electronics = "electronics"
    grooming = "grooming"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[ProductCategory] = mapped_column(
        SAEnum(ProductCategory, native_enum=False),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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
