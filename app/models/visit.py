import uuid
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDMixin


class Visit(UUIDMixin, CreatedAtMixin, Base):
    """Records a completed visit (visitor went to host's island)."""
    __tablename__ = "visits"

    queue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("queues.id"), nullable=False)
    island_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("islands.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    entered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    queue: Mapped["Queue"] = relationship("Queue", back_populates="visits")
    island: Mapped["Island"] = relationship("Island")
    user: Mapped["User"] = relationship("User", back_populates="visits")
    review: Mapped["Review | None"] = relationship("Review", back_populates="visit", uselist=False)

    def __repr__(self) -> str:
        return f"<Visit island={self.island_id} user={self.user_id}>"
