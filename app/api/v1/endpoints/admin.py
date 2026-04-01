import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v1.dependencies import require_admin, require_mod
from app.models.user import User
from app.models.ban import Ban
from app.models.strike import Strike
from app.schemas.ban import BanCreate, BanResponse
from app.schemas.strike import StrikeResponse

router = APIRouter(prefix="/admin", tags=["admin"])


# --- Bans ---

@router.post("/bans", response_model=BanResponse, status_code=status.HTTP_201_CREATED)
async def ban_user(
    body: BanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mod),
):
    user = await db.get(User, body.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check for existing active ban
    result = await db.execute(
        select(Ban).where(Ban.user_id == body.user_id, Ban.is_active == True)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already has an active ban")

    ban = Ban(
        user_id=body.user_id,
        banned_by_id=current_user.id,
        reason=body.reason,
        ban_from=body.ban_from,
        expires_at=body.expires_at,
    )
    db.add(ban)
    user.is_active = False
    await db.commit()
    await db.refresh(ban)
    return ban


@router.patch("/bans/{ban_id}/lift", response_model=BanResponse)
async def lift_ban(
    ban_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mod),
):
    ban = await db.get(Ban, ban_id)
    if not ban:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ban not found")
    if not ban.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ban is already inactive")

    ban.is_active = False
    ban.expires_at = datetime.now(timezone.utc)

    user = await db.get(User, ban.user_id)
    if user:
        user.is_active = True

    await db.commit()
    await db.refresh(ban)
    return ban


@router.get("/users/{user_id}/ban", response_model=BanResponse)
async def get_user_ban(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mod),
):
    result = await db.execute(select(Ban).where(Ban.user_id == user_id))
    ban = result.scalar_one_or_none()
    if not ban:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No ban found for this user")
    return ban


# --- Strikes ---

@router.post("/strikes", response_model=StrikeResponse, status_code=status.HTTP_201_CREATED)
async def add_strike(
    user_id: uuid.UUID,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mod),
):
    from app.models.strike import StrikeReason
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    strike = Strike(user_id=user_id, reason=reason)
    db.add(strike)
    await db.commit()
    await db.refresh(strike)
    return strike


@router.get("/users/{user_id}/strikes", response_model=list[StrikeResponse])
async def list_user_strikes(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mod),
):
    result = await db.execute(
        select(Strike).where(Strike.user_id == user_id).order_by(Strike.created_at.desc())
    )
    return result.scalars().all()