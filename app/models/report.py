import uuid
from sqlalchemy import Text, ForeignKey, Enum as SAEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin
import enum


class ReportReason(str, enum.Enum):
    scam = "scam"
    no_show = "no_show"
    rude_behavior = "rude_behavior"
    cheating = "cheating"
    other = "other"


class Report(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "reports"

    reporter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reported_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    reason: Mapped[ReportReason] = mapped_column(SAEnum(ReportReason), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    reporter = relationship("User", back_populates="reports_made", foreign_keys=[reporter_id])

    def __repr__(self) -> str:
        return f"<Report {self.reason} by={self.reporter_id} resolved={self.is_resolved}>"
