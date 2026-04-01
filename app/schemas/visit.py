import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class VisitResponse(BaseModel):
    id: uuid.UUID
    queue_id: uuid.UUID
    island_id: uuid.UUID
    user_id: uuid.UUID
    entered_at: datetime | None
    left_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)