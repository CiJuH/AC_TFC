import uuid
from sqlalchemy import ForeignKey, Enum as SAEnum, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin
import enum


class QueueUserStatus(str, enum.Enum):
    waiting = "waiting"
    visiting = "visiting"   # currently on the island
    skipped = "skipped"     # missed their turn once, gets a second chance
    done = "done"
    left = "left"           # left voluntarily
    kicked = "kicked"       # expelled after 2nd skip


class QueueUser(UUIDMixin, TimestampMixin, Base):
    """
    User entry into a queue.
    Position is determined by created_at (earliest = first in line).
    Skipped users are prioritized: ORDER BY status='skipped' DESC, created_at ASC.
    """
    __tablename__ = "queue_users"
    __table_args__ = (
        UniqueConstraint("queue_id", "user_id", name="uq_queue_user"),
        Index("ix_queue_users_status", "status"),
    )

    queue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("queues.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    status: Mapped[QueueUserStatus] = mapped_column(
        SAEnum(QueueUserStatus), default=QueueUserStatus.waiting, nullable=False
    )

    # Relationships
    queue: Mapped["Queue"] = relationship("Queue", back_populates="queue_users")
    user: Mapped["User"] = relationship("User", back_populates="queue_entries")

    def __repr__(self) -> str:
        return f"<QueueUser queue={self.queue_id} user={self.user_id} status={self.status}>"