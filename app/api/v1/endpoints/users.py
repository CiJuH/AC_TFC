import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.models.island import Island
from app.models.visit import Visit
from app.schemas.user import UserPublic, UserResponse, UserStats, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.username is not None:
        current_user.username = body.username
    if body.avatar_url is not None:
        current_user.avatar_url = body.avatar_url

    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.is_deleted = True
    current_user.is_active = False
    current_user.deleted_at = datetime.now(timezone.utc)
    await db.commit()


@router.get("/{user_id}/stats", response_model=UserStats)
async def get_user_stats(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user or user.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    island_row = await db.execute(
        select(Island)
        .where(Island.user_id == user_id, Island.deleted_at.is_(None))
        .limit(1)
    )
    island = island_row.scalar_one_or_none()

    visit_count_row = await db.execute(
        select(func.count()).select_from(Visit).where(Visit.user_id == user_id)
    )
    total_visits = visit_count_row.scalar()

    return UserStats(
        id=user.id,
        username=user.username,
        avatar_url=user.avatar_url,
        rating=user.rating,
        created_at=user.created_at,
        island=island,
        total_visits=total_visits,
    )


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user or user.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user