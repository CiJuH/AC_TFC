import uuid
from sqlalchemy import ForeignKey, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin
import enum


class FriendshipStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    blocked = "blocked"


class Friendship(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "friendships"
    __table_args__ = (UniqueConstraint("user_id", "friend_id", name="uq_friendship"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    friend_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    status: Mapped[FriendshipStatus] = mapped_column(
        SAEnum(FriendshipStatus), default=FriendshipStatus.pending, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="friendships_sent", foreign_keys=[user_id])
    friend: Mapped["User"] = relationship("User", back_populates="friendships_received", foreign_keys=[friend_id])

    def __repr__(self) -> str:
        return f"<Friendship {self.user_id} → {self.friend_id} [{self.status}]>"