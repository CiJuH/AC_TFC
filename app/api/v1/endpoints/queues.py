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
from app.schemas.queue import QueueBrowseItem, QueueCreate, QueueDetailResponse, QueueUpdate, QueueResponse
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


@router.get("/explore", response_model=list[QueueBrowseItem])
async def explore_queues(
    category: QueueCategory | None = None,
    turnip_price_min: int | None = None,
    turnip_price_max: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Active queues with island and host info. Optional filters, ordered by newest first."""
    participant_count_subq = (
        select(func.count())
        .where(
            QueueUser.queue_id == Queue.id,
            QueueUser.status.in_([QueueUserStatus.waiting, QueueUserStatus.skipped]),
        )
        .correlate(Queue)
        .scalar_subquery()
    )

    query = (
        select(Queue, Island, User, participant_count_subq.label("queue_count"))
        .join(Island, Queue.island_id == Island.id)
        .join(User, Island.user_id == User.id)
        .where(Queue.closed_at.is_(None), Queue.status == QueueStatus.active)
    )
    if category is not None:
        query = query.where(Queue.category == category)
    if turnip_price_min is not None:
        query = query.where(Queue.turnip_price >= turnip_price_min)
    if turnip_price_max is not None:
        query = query.where(Queue.turnip_price <= turnip_price_max)

    rows = (await db.execute(query.order_by(Queue.created_at.desc()))).all()

    return [
        QueueBrowseItem(
            island_id=island.id,
            island_name=island.island_name,
            host_name=user.username,
            host_avatar_url=user.avatar_url,
            host_rating=user.rating,
            queue_id=queue.id,
            category=queue.category.value,
            turnip_price=queue.turnip_price,
            description=queue.description,
            queue_count=queue_count,
            queue_limit=queue.limit,
            concurrent_visitors=queue.concurrent_visitors,
        )
        for queue, island, user, queue_count in rows
    ]


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

    # Mutual exclusion: host cannot be a visitor in another queue at the same time
    visitor_check = await db.execute(
        select(QueueUser).where(
            QueueUser.user_id == current_user.id,
            QueueUser.status.in_([QueueUserStatus.waiting, QueueUserStatus.visiting, QueueUserStatus.skipped]),
        )
    )
    if visitor_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No puedes abrir una cola mientras estás en la cola de otra isla"
        )

    queue = Queue(island_id=island.id, **body.model_dump())
    db.add(queue)
    await db.commit()
    await db.refresh(queue)
    return queue


@router.get("/{queue_id}/detail", response_model=QueueDetailResponse)
async def get_queue_detail(
    queue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns queue info combined with island and host data, plus participant counts.
    dodo_code is only revealed to the host or to visitors currently inside the island."""
    queue_count_subq = (
        select(func.count())
        .where(
            QueueUser.queue_id == queue_id,
            QueueUser.status.in_([QueueUserStatus.waiting, QueueUserStatus.skipped]),
        )
        .scalar_subquery()
    )
    visiting_count_subq = (
        select(func.count())
        .where(
            QueueUser.queue_id == queue_id,
            QueueUser.status == QueueUserStatus.visiting,
        )
        .scalar_subquery()
    )

    result = await db.execute(
        select(Queue, Island, User, queue_count_subq.label("queue_count"), visiting_count_subq.label("visiting_count"))
        .join(Island, Queue.island_id == Island.id)
        .join(User, Island.user_id == User.id)
        .where(Queue.id == queue_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Queue not found")

    queue, island, user, queue_count, visiting_count = row

    # Reveal dodo_code only to the host or to a user currently visiting
    is_host = island.user_id == current_user.id
    dodo_code: str | None = None
    if is_host:
        dodo_code = queue.dodo_code
    else:
        my_entry = await db.execute(
            select(QueueUser).where(
                QueueUser.queue_id == queue_id,
                QueueUser.user_id == current_user.id,
                QueueUser.status == QueueUserStatus.visiting,
            )
        )
        if my_entry.scalar_one_or_none():
            dodo_code = queue.dodo_code

    return QueueDetailResponse(
        queue_id=queue.id,
        status=queue.status.value,
        category=queue.category.value,
        turnip_price=queue.turnip_price,
        description=queue.description,
        queue_limit=queue.limit,
        concurrent_visitors=queue.concurrent_visitors,
        queue_count=queue_count,
        visiting_count=visiting_count,
        island_id=island.id,
        island_name=island.island_name,
        host_user_id=island.user_id,
        host_name=user.username,
        host_avatar_url=user.avatar_url,
        host_rating=user.rating,
        dodo_code=dodo_code,
    )


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

    # Expel all active participants when the host closes the island
    active = await db.execute(
        select(QueueUser).where(
            QueueUser.queue_id == queue_id,
            QueueUser.status.in_([
                QueueUserStatus.waiting,
                QueueUserStatus.visiting,
                QueueUserStatus.skipped,
            ]),
        )
    )
    for entry in active.scalars().all():
        entry.status = QueueUserStatus.left

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