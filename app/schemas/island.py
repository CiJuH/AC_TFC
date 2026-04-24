import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.island import Hemisphere, Fruit


class IslandPublic(BaseModel):
    """Island info shown on a user's public profile."""
    id: uuid.UUID
    island_name: str
    host_name: str
    hemisphere: Hemisphere
    fruit: Fruit
    description: str | None

    model_config = ConfigDict(from_attributes=True)


class IslandCreate(BaseModel):
    island_name: str
    host_name: str
    hemisphere: Hemisphere
    fruit: Fruit
    description: str | None = None


class IslandUpdate(BaseModel):
    island_name: str | None = None
    host_name: str | None = None
    hemisphere: Hemisphere | None = None
    fruit: Fruit | None = None
    description: str | None = None


class IslandResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    island_name: str
    host_name: str
    hemisphere: Hemisphere
    fruit: Fruit
    description: str | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)