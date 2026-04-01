from datetime import datetime
from sqlalchemy import String, Boolean, Float, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin
import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    visitor = "visitor"
    # "host" is not stored — it's derived: user is host if they have an active queue


class OAuthProvider(str, enum.Enum):
    discord = "discord"
    google = "google"
    email = "email"


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    # OAuth identity
    oauth_provider: Mapped[OAuthProvider] = mapped_column(SAEnum(OAuthProvider), nullable=False)
    oauth_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # Profile (populated from OAuth)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Status
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.visitor, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    islands: Mapped[list["Island"]] = relationship("Island", back_populates="user")
    queue_entries = relationship("QueueUser", back_populates="user")
    visits: Mapped[list["Visit"]] = relationship("Visit", back_populates="user")
    reviews_given: Mapped[list["Review"]] = relationship(
        "Review", back_populates="reviewer", foreign_keys="Review.reviewer_id"
    )
    reviews_received: Mapped[list["Review"]] = relationship(
        "Review", back_populates="reviewed", foreign_keys="Review.reviewed_id"
    )
    reports_made: Mapped[list["Report"]] = relationship(
        "Report", back_populates="reporter", foreign_keys="Report.reporter_id"
    )
    reports_received: Mapped[list["Report"]] = relationship(
        "Report", back_populates="reported", foreign_keys="Report.reported_id"
    )
    ban: Mapped["Ban | None"] = relationship("Ban", back_populates="user", uselist=False, foreign_keys="Ban.user_id")
    strikes: Mapped[list["Strike"]] = relationship("Strike", back_populates="user")
    friendships_sent: Mapped[list["Friendship"]] = relationship(
        "Friendship", back_populates="user", foreign_keys="Friendship.user_id"
    )
    friendships_received: Mapped[list["Friendship"]] = relationship(
        "Friendship", back_populates="friend", foreign_keys="Friendship.friend_id"
    )
    chats: Mapped[list["Chat"]] = relationship(
        "Chat",
        primaryjoin="or_(User.id == Chat.user_a_id, User.id == Chat.user_b_id)",
        viewonly=True,
    )
    messages_sent: Mapped[list["PrivateMessage"]] = relationship(
        "PrivateMessage", back_populates="sender", foreign_keys="PrivateMessage.sender_id"
    )

    @property
    def is_banned(self) -> bool:
        return self.ban is not None and self.ban.is_active

    def __repr__(self) -> str:
        return f"<User {self.username!r} ({self.role})>"
