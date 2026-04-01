import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PrivateMessageCreate(BaseModel):
    chat_id: uuid.UUID
    content: str


class PrivateMessageResponse(BaseModel):
    id: uuid.UUID
    chat_id: uuid.UUID
    sender_id: uuid.UUID
    content: str
    is_read: bool
    is_deleted: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)