import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CustomerProfile(Base):
    """Append-only snapshot of a customer's profile. No updated_at."""

    __tablename__ = "customer_profiles"

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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    visit_trigger: Mapped[str | None] = mapped_column(Text, nullable=True)
    opening_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    emotional_state: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
