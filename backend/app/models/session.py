import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SessionRole(enum.Enum):
    customer = "customer"
    businessman = "businessman"


class GameSession(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    role: Mapped[SessionRole] = mapped_column(
        SAEnum(SessionRole, native_enum=False),
        nullable=False,
    )
    # Circular FK: sessions ↔ customers. Deferred via use_alter so CREATE TABLE
    # order does not matter. ALTER TABLE is emitted after both tables exist.
    locked_npc_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey(
            "customers.id",
            use_alter=True,
            name="fk_sessions_locked_npc_id",
        ),
        nullable=True,
    )
    day_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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
