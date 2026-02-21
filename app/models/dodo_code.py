import uuid
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class DodoCode(UUIDMixin, TimestampMixin, Base):
    """
    Dodo codes are kept separate from Queue for privacy:
    only the current visitor (and host) should see it.
    """
    __tablename__ = "dodo_codes"

    queue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("queues.id"), unique=True, nullable=False
    )
    code: Mapped[str] = mapped_column(String(5), nullable=False)  # AC dodo codes are always 5 chars
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    queue = relationship("Queue", back_populates="dodo_code")

    def __repr__(self) -> str:
        return f"<DodoCode {self.code} active={self.is_active}>"
