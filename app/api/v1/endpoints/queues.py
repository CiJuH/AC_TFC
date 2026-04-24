import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.models.island import Island
from app.models.queue import Queue, QueueStatus, QueueCategory
from app.models.queue_users import QueueUser, QueueUserStatus
from app.schemas.queue import QueueCreate, QueueUpdate, QueueResponse
from app.schemas.queue_user import QueuePositionResponse

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


@router.get("/explore", response_model=list[QueueResponse])
async def explore_queues(
    category: QueueCategory | None = None,
    turnip_price_min: int | None = None,
    turnip_price_max: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Active queues with optional filters. Ordered by newest first."""
    query = select(Queue).where(
        Queue.closed_at.is_(None),
        Queue.status == QueueStatus.active,
    )
    if category is not None:
        query = query.where(Queue.category == category)
    if turnip_price_min is not None:
        query = query.where(Queue.turnip_price >= turnip_price_min)
    if turnip_price_max is not None:
        query = query.where(Queue.turnip_price <= turnip_price_max)
    result = await db.execute(query.order_by(Queue.created_at.desc()))
    return result.scalars().all()


@router.get("/turnip-prices", response_model=list[QueueResponse])
async def get_turnip_prices(db: AsyncSession = Depends(get_db)):
    """Active turnip queues ranked by price descending."""
    result = await db.execute(
        select(Queue).where(
            Queue.closed_at.is_(None),
            Queue.status == QueueStatus.active,
            Queue.category == QueueCategory.turnips,
            Queue.turnip_price.is_not(None),
        ).order_by(Queue.turnip_price.desc())
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


@router.get("/{queue_id}/my-position", response_model=QueuePositionResponse)
async def get_my_position(
    queue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(QueueUser).where(
            QueueUser.queue_id == queue_id,
            QueueUser.user_id == current_user.id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You are not in this queue")

    if entry.status not in (QueueUserStatus.waiting, QueueUserStatus.skipped):
        return QueuePositionResponse(queue_user_id=entry.id, status=entry.status, position=None)

    if entry.status == QueueUserStatus.skipped:
        # Skipped users go first; count skipped entries that joined before this one
        ahead = await db.execute(
            select(func.count()).where(
                QueueUser.queue_id == queue_id,
                QueueUser.status == QueueUserStatus.skipped,
                QueueUser.created_at < entry.created_at,
            )
        )
        position = ahead.scalar() + 1
    else:
        # Waiting: all skipped users are ahead, then waiting by join time
        skipped_count = await db.execute(
            select(func.count()).where(
                QueueUser.queue_id == queue_id,
                QueueUser.status == QueueUserStatus.skipped,
            )
        )
        waiting_ahead = await db.execute(
            select(func.count()).where(
                QueueUser.queue_id == queue_id,
                QueueUser.status == QueueUserStatus.waiting,
                QueueUser.created_at < entry.created_at,
            )
        )
        position = skipped_count.scalar() + waiting_ahead.scalar() + 1

    return QueuePositionResponse(queue_user_id=entry.id, status=entry.status, position=position)