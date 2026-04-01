import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin
import enum


class Hemisphere(str, enum.Enum):
    north = "north"
    south = "south"


class Fruit(str, enum.Enum):
    apple = "apple"
    pear = "pear"
    cherry = "cherry"
    peach = "peach"
    orange = "orange"


class Island(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "islands"

    # Owner
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Island identity
    island_name : Mapped[str] = mapped_column(String(128), nullable=False)
    host_name: Mapped[str] = mapped_column(String(64), nullable=False)

    # Island properties
    hemisphere: Mapped[Hemisphere] = mapped_column(SAEnum(Hemisphere), nullable=False)
    fruit: Mapped[Fruit] = mapped_column(SAEnum(Fruit), nullable=False)

    # Description
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="islands")
    queues: Mapped[list["Queue"]] = relationship("Queue", back_populates="island")

    def __repr__(self) -> str:
        return f"<Island {self.island_name!r} owner={self.user_id}>"
