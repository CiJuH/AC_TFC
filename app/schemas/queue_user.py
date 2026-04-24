import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.queue_users import QueueUserStatus


class QueueUserCreate(BaseModel):
    queue_id: uuid.UUID


class QueueUserResponse(BaseModel):
    id: uuid.UUID
    queue_id: uuid.UUID
    user_id: uuid.UUID
    status: QueueUserStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QueuePositionResponse(BaseModel):
    queue_user_id: uuid.UUID
    status: QueueUserStatus
    position: int | None  # None when not waiting or skipped