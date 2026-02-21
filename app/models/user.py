from sqlalchemy import String, Boolean, Enum as SAEnum
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


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    # OAuth identity
    oauth_provider: Mapped[OAuthProvider] = mapped_column(SAEnum(OAuthProvider), nullable=False)
    oauth_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)

    # Profile (populated from OAuth)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    island_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Role & status
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.visitor, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    queues = relationship("Queue", back_populates="host", foreign_keys="Queue.host_id")
    queue_entries = relationship("QueueUser", back_populates="user")
    turnip_prices = relationship("TurnipPrice", back_populates="user")
    visits_as_host = relationship("Visit", back_populates="host", foreign_keys="Visit.host_id")
    visits_as_visitor = relationship("Visit", back_populates="visitor", foreign_keys="Visit.visitor_id")
    reviews_given = relationship("Review", back_populates="reviewer", foreign_keys="Review.reviewer_id")
    reviews_received = relationship("Review", back_populates="reviewed", foreign_keys="Review.reviewed_id")
    reports_made = relationship("Report", back_populates="reporter", foreign_keys="Report.reporter_id")
    ban = relationship("Ban", back_populates="user", uselist=False)

    @property
    def is_host(self) -> bool:
        """A user is considered a host if they have an active queue."""
        return any(q.is_active for q in self.queues)

    @property
    def is_banned(self) -> bool:
        return self.ban is not None and self.ban.is_active

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"
