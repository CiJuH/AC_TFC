import uuid
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class Visit(UUIDMixin, TimestampMixin, Base):
    """Records a completed visit (visitor went to host's island)."""
    __tablename__ = "visits"

    queue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("queues.id"), nullable=False)
    host_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    visitor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    queue = relationship("Queue", back_populates="visits")
    host = relationship("User", back_populates="visits_as_host", foreign_keys=[host_id])
    visitor = relationship("User", back_populates="visits_as_visitor", foreign_keys=[visitor_id])
    review = relationship("Review", back_populates="visit", uselist=False)

    def __repr__(self) -> str:
        return f"<Visit host={self.host_id} visitor={self.visitor_id}>"
