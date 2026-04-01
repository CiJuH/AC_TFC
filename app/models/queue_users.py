import uuid
from datetime import datetime, timezone
from sqlalchemy import Integer, DateTime, ForeignKey, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin
import enum


class QueueUserStatus(str, enum.Enum):
    waiting = "waiting"
    visiting = "visiting"   # currently on the island
    done = "done"
    skipped = "skipped"
    left = "left"


class QueueUser(UUIDMixin, TimestampMixin, Base):
    """ 
    User entry inot a queue.
    The position is calculated using created_at (not stored as a fixed int).
    """
    __tablename__ = "queue_users"
    __table_args__ = (UniqueConstraint("queue_id", "user_id", name="uq_queue_user"),)

    # Queue context
    queue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("queues.id"), nullable=False
    )

    # Participant
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Queue state
    status: Mapped[QueueUserStatus] = mapped_column(
        SAEnum(QueueUserStatus), default=QueueUserStatus.waiting, nullable=False
    )

    # Relationships
    queue = relationship("Queue", back_populates="queue_users")
    user = relationship("User", back_populates="queue_entries")

    def __repr__(self) -> str:
        return f"<QueueUser queue={self.queue_id} user={self.user_id} status={self.status}>"
