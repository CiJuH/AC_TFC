import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator
from app.models.queue import QueueStatus, QueueCategory


class QueueCreate(BaseModel):
    category: QueueCategory
    dodo_code: str
    turnip_price: int | None = None  # required if category = turnips
    description: str | None = None
    limit: int = 10
    requires_fee: bool = False
    fee_description: str | None = None
    visit_ends_at: datetime | None = None

    @field_validator("dodo_code")
    @classmethod
    def dodo_code_must_be_5_chars(cls, v: str) -> str:
        if len(v) != 5:
            raise ValueError("Dodo code must be exactly 5 characters")
        return v.upper()

    @field_validator("limit")
    @classmethod
    def limit_must_be_valid(cls, v: int) -> int:
        if not 1 <= v <= 100:
            raise ValueError("Limit must be between 1 and 100")
        return v


class QueueUpdate(BaseModel):
    status: QueueStatus | None = None
    dodo_code: str | None = None
    limit: int | None = None
    visit_ends_at: datetime | None = None

    @field_validator("dodo_code")
    @classmethod
    def dodo_code_must_be_5_chars(cls, v: str | None) -> str | None:
        if v is not None and len(v) != 5:
            raise ValueError("Dodo code must be exactly 5 characters")
        return v.upper() if v else v

    @field_validator("limit")
    @classmethod
    def limit_must_be_valid(cls, v: int | None) -> int | None:
        if v is not None and not 1 <= v <= 100:
            raise ValueError("Limit must be between 1 and 100")
        return v


class QueueResponse(BaseModel):
    id: uuid.UUID
    island_id: uuid.UUID
    category: QueueCategory
    turnip_price: int | None
    description: str | None
    dodo_code: str
    status: QueueStatus
    limit: int
    requires_fee: bool
    fee_description: str | None
    visit_ends_at: datetime | None
    closed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)