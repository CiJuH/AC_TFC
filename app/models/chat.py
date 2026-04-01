import uuid
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from app.models.mixins import UUIDMixin, CreatedAtMixin


class Chat(UUIDMixin, CreatedAtMixin, Base):
    """A chat room between two users (DMs)."""
    __tablename__ = "chats"
    __table_args__ = (UniqueConstraint("user_a_id", "user_b_id", name="uq_chat_users"),)

    user_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    user_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user_a: Mapped["User"] = relationship("User", foreign_keys=[user_a_id])
    user_b: Mapped["User"] = relationship("User", foreign_keys=[user_b_id])
    messages: Mapped[list["PrivateMessage"]] = relationship(
        "PrivateMessage", back_populates="chat", order_by="PrivateMessage.created_at"
    )

    def __repr__(self) -> str:
        return f"<Chat {self.user_a_id} ↔ {self.user_b_id}>"
