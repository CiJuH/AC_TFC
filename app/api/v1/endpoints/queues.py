import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.models.island import Island
from app.models.queue import Queue, QueueStatus
from app.schemas.queue import QueueCreate, QueueUpdate, QueueResponse

router = APIRouter(prefix="/queues", tags=["queues"])


async def _get_user_island(db: AsyncSession, user_id: uuid.UUID) -> Island:
    """Returns the active island of the user, or raises 404."""
    result = await db.execute(
        select(Island).where(Island.user_id == user_id, Island.deleted_at.is_(None))
    )
    island = result.scalar_one_or_none()
    if not island:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You don't have an island")
    return island


async def _get_queue_as_host(db: AsyncSession, queue_id: uuid.UUID, user_id: uuid.UUID) -> Queue:
    """Returns the queue if the current user owns the island it belongs to, or raises 403/404."""
    queue = await db.get(Queue, queue_id)
    if not queue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Queue not found")

    island = await db.get(Island, queue.island_id)
    if not island or island.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your queue")
    return queue


@router.get("/my", response_model=list[QueueResponse])
async def get_my_queues(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    island = await _get_user_island(db, current_user.id)
    result = await db.execute(
        select(Queue).where(Queue.island_id == island.id).order_by(Queue.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=QueueResponse, status_code=status.HTTP_201_CREATED)
async def create_queue(
    body: QueueCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    island = await _get_user_island(db, current_user.id)

    # Only one active queue per island at a time
    result = await db.execute(
        select(Queue).where(Queue.island_id == island.id, Queue.closed_at.is_(None))
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Island already has an open queue")

    queue = Queue(island_id=island.id, **body.model_dump())
    db.add(queue)
    await db.commit()
    await db.refresh(queue)
    return queue


@router.get("/{queue_id}", response_model=QueueResponse)
async def get_queue(queue_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    queue = await db.get(Queue, queue_id)
    if not queue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Queue not found")
    return queue


@router.patch("/{queue_id}", response_model=QueueResponse)
async def update_queue(
    queue_id: uuid.UUID,
    body: QueueUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    queue = await _get_queue_as_host(db, queue_id, current_user.id)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(queue, field, value)

    await db.commit()
    await db.refresh(queue)
    return queue


@router.post("/{queue_id}/close", response_model=QueueResponse)
async def close_queue(
    queue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    queue = await _get_queue_as_host(db, queue_id, current_user.id)

    if queue.closed_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Queue is already closed")

    queue.status = QueueStatus.closed
    queue.closed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(queue)
    return queue