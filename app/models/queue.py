import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDMixin
import enum


class QueueStatus(str, enum.Enum):
    active = "active"   # accepting visitors
    paused = "paused"   # host paused temporaly
    closed = "closed"   # closed definitively


class QueueCategory(str, enum.Enum):
    turnips = "turnips"
    objects = "objects"


class Queue(UUIDMixin, CreatedAtMixin, Base):
    """
    The active queue related to the island.
    Doesn't use TimestampMixin because only has created_at and closed_at (not updated_at).
    """
    __tablename__ = "queues"

    # Island
    island_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("islands.id"), nullable=False
    )

    # Event info
    category: Mapped[QueueCategory] = mapped_column(SAEnum(QueueCategory), nullable=False)
    turnip_price: Mapped[int] = mapped_column(Integer, nullable=True)  # bells per turnip
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    dodo_code: Mapped[str] = mapped_column(String(5), nullable=False)

    # Queue settings
    status: Mapped[QueueStatus] = mapped_column(SAEnum(QueueStatus), default=QueueStatus.active, nullable=False)
    limit: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    # Timestamps
    visit_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True) # Estimated closing time
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True) # None = open

    # Fees
    requires_fee: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fee_description: Mapped[str | None] = mapped_column(String(256), nullable=True)  # e.g. "1 NMT" or "tip appreciated"

    @property
    def is_active(self) -> bool:
        return self.status == QueueStatus.open

    # Relationships
    island: Mapped["Island"] = relationship("Island", back_populates="queues")
    queue_users: Mapped[list["QueueUser"]] = relationship(
        "QueueUser", back_populates="queue", order_by="QueueUser.created_at"
    )
    messages: Mapped[list["QueueMessage"]] = relationship("QueueMessage", back_populates="queue")
    visits: Mapped[list["Visit"]] = relationship("Visit", back_populates="queue")

    def __repr__(self) -> str:
        return f"<Queue island={self.island_id} category={self.category} status={self.status}>"
