import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class QueueMessageCreate(BaseModel):
    queue_id: uuid.UUID
    content: str


class QueueMessageResponse(BaseModel):
    id: uuid.UUID
    queue_id: uuid.UUID
    sender_id: uuid.UUID
    content: str
    is_pinned: bool
    is_deleted: bool
    deleted_by: uuid.UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)