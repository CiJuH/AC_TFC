import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from app.models.mixins import UUIDMixin, CreatedAtMixin
import enum


class StrikeReason(str, enum.Enum):
    no_confirmation = "no_confirmation"     # user didn't confirmt their turn in the limit time
    kicked_by_host = "kicked_by_host"       # host expulsed the user manually


class Strike(UUIDMixin, CreatedAtMixin, Base):
    __tablename__ = "strikes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    reason: Mapped[StrikeReason] = mapped_column(SAEnum(StrikeReason), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="strikes")

    def __repr__(self) -> str:
        return f"<Strike user={self.user_id} reason={self.reason}>"
