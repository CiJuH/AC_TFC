import uuid
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class Chat(UUIDMixin, TimestampMixin, Base):
    """A chat room between two users (DMs)."""
    __tablename__ = "chats"
    __table_args__ = (UniqueConstraint("user_a_id", "user_b_id", name="uq_chat_users"),)

    user_a_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user_b_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    messages = relationship("Message", back_populates="chat", order_by="Message.created_at")

    def __repr__(self) -> str:
        return f"<Chat {self.user_a_id} ↔ {self.user_b_id}>"
