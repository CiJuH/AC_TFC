import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.models.friendship import Friendship, FriendshipStatus
from app.schemas.friendship import FriendshipCreate, FriendshipUpdate, FriendshipResponse

router = APIRouter(prefix="/friendships", tags=["friendships"])


@router.get("", response_model=list[FriendshipResponse])
async def list_friendships(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Friendship).where(
            or_(Friendship.user_id == current_user.id, Friendship.friend_id == current_user.id)
        )
    )
    return result.scalars().all()


@router.post("", response_model=FriendshipResponse, status_code=status.HTTP_201_CREATED)
async def send_friend_request(
    body: FriendshipCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.friend_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot add yourself")

    friend = await db.get(User, body.friend_id)
    if not friend or not friend.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if friendship already exists in either direction
    result = await db.execute(
        select(Friendship).where(
            or_(
                (Friendship.user_id == current_user.id) & (Friendship.friend_id == body.friend_id),
                (Friendship.user_id == body.friend_id) & (Friendship.friend_id == current_user.id),
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Friendship already exists")

    friendship = Friendship(user_id=current_user.id, friend_id=body.friend_id)
    db.add(friendship)
    await db.commit()
    await db.refresh(friendship)
    return friendship


@router.patch("/{friendship_id}", response_model=FriendshipResponse)
async def update_friendship(
    friendship_id: uuid.UUID,
    body: FriendshipUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    friendship = await db.get(Friendship, friendship_id)
    if not friendship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friendship not found")

    # Only the receiver can accept; both sides can block
    if body.status == FriendshipStatus.accepted and friendship.friend_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the receiver can accept")
    if current_user.id not in (friendship.user_id, friendship.friend_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your friendship")

    friendship.status = body.status
    await db.commit()
    await db.refresh(friendship)
    return friendship


@router.delete("/{friendship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_friendship(
    friendship_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    friendship = await db.get(Friendship, friendship_id)
    if not friendship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friendship not found")
    if current_user.id not in (friendship.user_id, friendship.friend_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your friendship")

    await db.delete(friendship)
    await db.commit()