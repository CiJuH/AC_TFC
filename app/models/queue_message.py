import uuid
from datetime import datetime, timezone
from sqlalchemy import Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from app.models.mixins import UUIDMixin, CreatedAtMixin


class QueueMessage(UUIDMixin, CreatedAtMixin, Base):
    """
    Message in the queue chat (visible to all participants).
    """
    __tablename__ = "queue_messages"

    # Queue context
    queue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("queues.id"), nullable=False
    )

    # Author
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Message content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Moderation / deletion
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Relationship
    queue: Mapped["Queue"] = relationship("Queue", back_populates="messages")
    sender: Mapped["User"] = relationship("User", foreign_keys=[sender_id])
    deleter: Mapped["User | None"] = relationship("User", foreign_keys=[deleted_by])

    def __repr__(self) -> str:
        return f"<QueueMessage queue={self.queue_id} sender={self.sender_id} pinned={self.is_pinned}>"