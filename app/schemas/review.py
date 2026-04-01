import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator


class ReviewCreate(BaseModel):
    visit_id: uuid.UUID
    reviewed_id: uuid.UUID
    rating: int
    comment: str | None = None

    @field_validator("rating")
    @classmethod
    def rating_must_be_valid(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class ReviewResponse(BaseModel):
    id: uuid.UUID
    visit_id: uuid.UUID
    reviewer_id: uuid.UUID
    reviewed_id: uuid.UUID
    rating: int
    comment: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)