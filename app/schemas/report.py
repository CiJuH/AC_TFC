import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.report import ReportReason


class ReportCreate(BaseModel):
    reported_id: uuid.UUID
    reason: ReportReason
    description: str | None = None


class ReportResponse(BaseModel):
    id: uuid.UUID
    reporter_id: uuid.UUID
    reported_id: uuid.UUID
    reason: ReportReason
    description: str | None
    is_resolved: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)