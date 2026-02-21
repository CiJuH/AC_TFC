import uuid
from sqlalchemy import String, Boolean, Integer, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin
import enum


class QueueStatus(str, enum.Enum):
    open = "open"
    paused = "paused"
    closed = "closed"


class Queue(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "queues"

    host_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Turnip info
    turnip_price: Mapped[int] = mapped_column(Integer, nullable=False)  # bells per turnip
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Queue settings
    status: Mapped[QueueStatus] = mapped_column(SAEnum(QueueStatus), default=QueueStatus.open, nullable=False)
    max_visitors: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    requires_fee: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fee_description: Mapped[str | None] = mapped_column(String(256), nullable=True)  # e.g. "1 NMT" or "tip appreciated"

    @property
    def is_active(self) -> bool:
        return self.status == QueueStatus.open

    # Relationships
    host = relationship("User", back_populates="queues", foreign_keys=[host_id])
    queue_users = relationship("QueueUser", back_populates="queue", order_by="QueueUser.position")
    dodo_code = relationship("DodoCode", back_populates="queue", uselist=False)
    visits = relationship("Visit", back_populates="queue")

    def __repr__(self) -> str:
        return f"<Queue {self.id} - {self.turnip_price}🔔 [{self.status}]>"
