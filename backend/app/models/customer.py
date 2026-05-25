import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CustomerArchetype(enum.Enum):
    bargain_hunter = "bargain_hunter"
    festival_shopper = "festival_shopper"
    loyal_regular = "loyal_regular"
    impulse_buyer = "impulse_buyer"
    difficult_returner = "difficult_returner"
    gift_buyer = "gift_buyer"
    tech_savvy_browser = "tech_savvy_browser"


class CustomerChannel(enum.Enum):
    online = "online"
    offline = "offline"


class CustomerStage(enum.Enum):
    home = "home"
    browsing = "browsing"
    checkout = "checkout"
    payment = "payment"
    post_purchase = "post_purchase"


class CustomerEmotionalTone(enum.Enum):
    calm = "calm"
    frustrated = "frustrated"
    excited = "excited"
    hesitant = "hesitant"


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        Index(
            "ix_customers_session_is_user_controlled",
            "session_id",
            "is_user_controlled",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sessions.id"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    archetype: Mapped[CustomerArchetype] = mapped_column(
        SAEnum(CustomerArchetype, native_enum=False),
        nullable=False,
    )
    channel: Mapped[CustomerChannel] = mapped_column(
        SAEnum(CustomerChannel, native_enum=False),
        nullable=False,
    )
    current_stage: Mapped[CustomerStage] = mapped_column(
        SAEnum(CustomerStage, native_enum=False),
        nullable=False,
        default=CustomerStage.home,
    )
    emotional_tone: Mapped[CustomerEmotionalTone] = mapped_column(
        SAEnum(CustomerEmotionalTone, native_enum=False),
        nullable=False,
        default=CustomerEmotionalTone.calm,
    )
    is_user_controlled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    intent: Mapped[str | None] = mapped_column(Text, nullable=True)
    budget: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2), nullable=True)
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
