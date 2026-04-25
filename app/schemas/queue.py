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
    concurrent_visitors: int = 4
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

    @field_validator("concurrent_visitors")
    @classmethod
    def concurrent_visitors_must_be_valid(cls, v: int) -> int:
        if not 1 <= v <= 7:
            raise ValueError("concurrent_visitors must be between 1 and 7 (ACNH limit)")
        return v


class QueueUpdate(BaseModel):
    status: QueueStatus | None = None
    dodo_code: str | None = None
    limit: int | None = None
    concurrent_visitors: int | None = None
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

    @field_validator("concurrent_visitors")
    @classmethod
    def concurrent_visitors_must_be_valid(cls, v: int | None) -> int | None:
        if v is not None and not 1 <= v <= 7:
            raise ValueError("concurrent_visitors must be between 1 and 7 (ACNH limit)")
        return v


class QueueBrowseItem(BaseModel):
    island_id: uuid.UUID
    island_name: str
    host_name: str
    host_avatar_url: str | None
    host_rating: float
    queue_id: uuid.UUID
    category: str
    turnip_price: int | None
    description: str | None
    queue_count: int
    queue_limit: int
    concurrent_visitors: int

    model_config = ConfigDict(from_attributes=False)


class QueueResponse(BaseModel):
    id: uuid.UUID
    island_id: uuid.UUID
    category: QueueCategory
    turnip_price: int | None
    description: str | None
    dodo_code: str
    status: QueueStatus
    limit: int
    concurrent_visitors: int
    requires_fee: bool
    fee_description: str | None
    visit_ends_at: datetime | None
    closed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QueueDetailResponse(BaseModel):
    queue_id: uuid.UUID
    status: str
    category: str
    turnip_price: int | None
    description: str | None
    queue_limit: int
    concurrent_visitors: int
    queue_count: int      # waiting + visiting
    visiting_count: int   # currently inside the island
    island_id: uuid.UUID
    island_name: str
    host_name: str
    host_avatar_url: str | None
    host_rating: float
    dodo_code: str | None  # only revealed to visiting users and the host

    model_config = ConfigDict(from_attributes=False)