import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ChatCreate(BaseModel):
    friend_id: uuid.UUID


class ChatResponse(BaseModel):
    id: uuid.UUID
    user_a_id: uuid.UUID
    user_b_id: uuid.UUID
    last_message_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)