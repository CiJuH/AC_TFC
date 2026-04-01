import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BanCreate(BaseModel):
    user_id: uuid.UUID
    reason: str
    ban_from: datetime
    expires_at: datetime | None = None  # None = permanent


class BanResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    banned_by_id: uuid.UUID | None
    reason: str
    ban_from: datetime
    is_active: bool
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)