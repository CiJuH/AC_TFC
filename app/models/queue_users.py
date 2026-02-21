import uuid
from sqlalchemy import Integer, ForeignKey, Enum as SAEnum, UniqueConstraint
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
    __tablename__ = "queue_users"
    __table_args__ = (UniqueConstraint("queue_id", "user_id", name="uq_queue_user"),)

    queue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("queues.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[QueueUserStatus] = mapped_column(
        SAEnum(QueueUserStatus), default=QueueUserStatus.waiting, nullable=False
    )

    # Relationships
    queue = relationship("Queue", back_populates="queue_users")
    user = relationship("User", back_populates="queue_entries")

    def __repr__(self) -> str:
        return f"<QueueUser pos={self.position} status={self.status}>"
