import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.strike import StrikeReason


class StrikeResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    reason: StrikeReason
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)