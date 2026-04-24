import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v1.dependencies import get_current_user
from app.api.v1.helpers import check_auto_ban
from app.models.user import User
from app.models.island import Island
from app.models.queue import Queue, QueueStatus
from app.models.queue_users import QueueUser, QueueUserStatus
from app.models.strike import Strike, StrikeReason
from app.schemas.queue_user import QueueUserResponse, ActiveQueueStatusResponse

router = APIRouter(tags=["queue users"])


async def _get_queue_or_404(db: AsyncSession, queue_id: uuid.UUID) -> Queue:
    queue = await db.get(Queue, queue_id)
    if not queue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Queue not found")
    return queue


async def _is_host(db: AsyncSession, queue: Queue, user_id: uuid.UUID) -> bool:
    island = await db.get(Island, queue.island_id)
    return island is not None and island.user_id == user_id


@router.get("/queues/{queue_id}/participants", response_model=list[QueueUserResponse])
async def list_participants(queue_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Returns participants ordered by position (join time)."""
    result = await db.execute(
        select(QueueUser)
        .where(QueueUser.queue_id == queue_id)
        .order_by(QueueUser.created_at)
    )
    return result.scalars().all()


@router.post("/queues/{queue_id}/join", response_model=QueueUserResponse, status_code=status.HTTP_201_CREATED)
async def join_queue(
    queue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    queue = await _get_queue_or_404(db, queue_id)

    if queue.status != QueueStatus.active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Queue is not active")
    if queue.closed_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Queue is closed")

    # Check if already in this queue
    result = await db.execute(
        select(QueueUser).where(QueueUser.queue_id == queue_id, QueueUser.user_id == current_user.id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already in this queue")

    # Check queue capacity (only count waiting/visiting)
    count_result = await db.execute(
        select(func.count()).where(
            QueueUser.queue_id == queue_id,
            QueueUser.status.in_([QueueUserStatus.waiting, QueueUserStatus.visiting]),
        )
    )
    if count_result.scalar() >= queue.limit:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Queue is full")

    entry = QueueUser(queue_id=queue_id, user_id=current_user.id)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.post("/queues/{queue_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_queue(
    queue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(QueueUser).where(
            QueueUser.queue_id == queue_id,
            QueueUser.user_id == current_user.id,
            QueueUser.status.in_([QueueUserStatus.waiting, QueueUserStatus.visiting]),
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You are not in this queue")

    entry.status = QueueUserStatus.left
    await db.commit()


@router.post("/queues/{queue_id}/rejoin", response_model=QueueUserResponse)
async def rejoin_queue(
    queue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Visitor confirms second chance after being skipped, moving back to waiting."""
    queue = await _get_queue_or_404(db, queue_id)
    if queue.status != QueueStatus.active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Queue is not active")

    result = await db.execute(
        select(QueueUser).where(
            QueueUser.queue_id == queue_id,
            QueueUser.user_id == current_user.id,
            QueueUser.status == QueueUserStatus.skipped,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No pending second chance in this queue")

    entry.status = QueueUserStatus.waiting
    await db.commit()
    await db.refresh(entry)
    return entry


@router.patch("/queues/{queue_id}/participants/{user_id}", response_model=QueueUserResponse)
async def update_participant_status(
    queue_id: uuid.UUID,
    user_id: uuid.UUID,
    new_status: QueueUserStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Host-only: change a participant's status (visiting, done, skipped)."""
    queue = await _get_queue_or_404(db, queue_id)

    if not await _is_host(db, queue, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the host can do this")

    result = await db.execute(
        select(QueueUser).where(QueueUser.queue_id == queue_id, QueueUser.user_id == user_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")

    # Skip flow: second skip → kick + strike
    if new_status == QueueUserStatus.skipped and entry.status == QueueUserStatus.skipped:
        entry.status = QueueUserStatus.kicked
        db.add(Strike(user_id=user_id, reason=StrikeReason.no_confirmation))
        await db.commit()
        await check_auto_ban(db, user_id)
    else:
        entry.status = new_status
        await db.commit()

    await db.refresh(entry)
    return entry


@router.get("/queue-users/me/active", response_model=ActiveQueueStatusResponse)
async def get_my_active_queue_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the queue the current user is currently waiting in or visiting."""
    result = await db.execute(
        select(QueueUser).where(
            QueueUser.user_id == current_user.id,
            QueueUser.status.in_([
                QueueUserStatus.waiting,
                QueueUserStatus.visiting,
                QueueUserStatus.skipped,
            ]),
        )
    )
    queue_user = result.scalar_one_or_none()
    if not queue_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not in any active queue")

    queue = await db.get(Queue, queue_user.queue_id)
    island = await db.get(Island, queue.island_id)

    # Count total waiting + visiting
    total = (await db.execute(
        select(func.count()).where(
            QueueUser.queue_id == queue.id,
            QueueUser.status.in_([QueueUserStatus.waiting, QueueUserStatus.visiting]),
        )
    )).scalar()

    # Position: skipped first, then waiting by created_at. None if already visiting.
    position = None
    if queue_user.status != QueueUserStatus.visiting:
        skipped_ahead = (await db.execute(
            select(func.count()).where(
                QueueUser.queue_id == queue.id,
                QueueUser.status == QueueUserStatus.skipped,
                QueueUser.id != queue_user.id,
            )
        )).scalar()

        if queue_user.status == QueueUserStatus.skipped:
            before_me = (await db.execute(
                select(func.count()).where(
                    QueueUser.queue_id == queue.id,
                    QueueUser.status == QueueUserStatus.skipped,
                    QueueUser.created_at < queue_user.created_at,
                )
            )).scalar()
            position = before_me + 1
        else:
            waiting_before_me = (await db.execute(
                select(func.count()).where(
                    QueueUser.queue_id == queue.id,
                    QueueUser.status == QueueUserStatus.waiting,
                    QueueUser.created_at < queue_user.created_at,
                )
            )).scalar()
            position = skipped_ahead + waiting_before_me + 1

    return ActiveQueueStatusResponse(
        queue_user_id=queue_user.id,
        queue_id=queue.id,
        island_id=island.id,
        island_name=island.island_name,
        status=queue_user.status,
        position=position,
        total=total,
        category=queue.category.value,
        turnip_price=queue.turnip_price,
    )