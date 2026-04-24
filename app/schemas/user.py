import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.user import UserRole, OAuthProvider
from app.schemas.island import IslandPublic


class UserPublic(BaseModel):
    """Minimal user info shown in queues, messages, reviews, etc."""
    id: uuid.UUID
    username: str
    avatar_url: str | None
    rating: float

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """Full user info returned to the authenticated user."""
    id: uuid.UUID
    username: str
    avatar_url: str | None
    rating: float
    role: UserRole
    oauth_provider: OAuthProvider
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    username: str | None = None
    avatar_url: str | None = None


class UserStats(BaseModel):
    """Aggregated profile data for a public user view."""
    id: uuid.UUID
    username: str
    avatar_url: str | None
    rating: float
    created_at: datetime
    island: IslandPublic | None
    total_visits: int

    model_config = ConfigDict(from_attributes=True)