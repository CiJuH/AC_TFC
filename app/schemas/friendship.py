import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.friendship import FriendshipStatus


class FriendshipCreate(BaseModel):
    friend_id: uuid.UUID


class FriendshipUpdate(BaseModel):
    status: FriendshipStatus


class FriendshipResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    friend_id: uuid.UUID
    status: FriendshipStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)