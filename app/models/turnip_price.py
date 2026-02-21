import uuid
from datetime import datetime
from sqlalchemy import Integer, ForeignKey, Enum as SAEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin
import enum


class PriceSlot(str, enum.Enum):
    """AC prices change twice a day Mon-Sat"""
    monday_am = "monday_am"
    monday_pm = "monday_pm"
    tuesday_am = "tuesday_am"
    tuesday_pm = "tuesday_pm"
    wednesday_am = "wednesday_am"
    wednesday_pm = "wednesday_pm"
    thursday_am = "thursday_am"
    thursday_pm = "thursday_pm"
    friday_am = "friday_am"
    friday_pm = "friday_pm"
    saturday_am = "saturday_am"
    saturday_pm = "saturday_pm"


class TurnipPrice(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "turnip_prices"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    buy_price: Mapped[int | None] = mapped_column(Integer, nullable=True)   # Sunday buy price
    sell_price: Mapped[int] = mapped_column(Integer, nullable=False)        # Current sell price
    slot: Mapped[PriceSlot] = mapped_column(SAEnum(PriceSlot), nullable=False)
    week_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # Sunday of that week

    # Relationships
    user = relationship("User", back_populates="turnip_prices")

    def __repr__(self) -> str:
        return f"<TurnipPrice {self.sell_price}🔔 [{self.slot}]>"
