import uuid
from datetime import datetime
from sqlalchemy import Text, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class Ban(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "bans"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    banned_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    ban_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)  # None = permanent

    # Relationships
    user = relationship("User", back_populates="ban", foreign_keys=[user_id])
    banned_by = relationship("User", foreign_keys=[banned_by_id])

    def __repr__(self) -> str:
        return f"<Ban user={self.user_id} active={self.is_active}>"
