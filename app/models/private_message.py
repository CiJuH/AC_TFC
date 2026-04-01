import uuid
from datetime import datetime, timezone
from sqlalchemy import Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from app.models.mixins import UUIDMixin, CreatedAtMixin


class PrivateMessage(UUIDMixin, CreatedAtMixin, Base):
    """
    Direct message between two users.
    """
    __tablename__ = "private_messages"

    chat_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=False)
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="messages_sent")

    def __repr__(self) -> str:
        return f"<PrivateMessage chat={self.chat_id} sender={self.sender_id} read={self.is_read}>"
