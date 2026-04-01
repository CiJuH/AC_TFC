import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.models.island import Island
from app.models.queue import Queue
from app.models.queue_users import QueueUser, QueueUserStatus
from app.models.visit import Visit
from app.schemas.visit import VisitResponse

router = APIRouter(prefix="/visits", tags=["visits"])


@router.post("", response_model=VisitResponse, status_code=status.HTTP_201_CREATED)
async def start_visit(
    queue_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Host marks a visitor as entering the island. Creates a Visit record."""
    queue = await db.get(Queue, queue_id)
    if not queue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Queue not found")

    # Only the host can start a visit
    island = await db.get(Island, queue.island_id)
    if not island or island.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the host can do this")

    # Update QueueUser status to visiting
    result = await db.execute(
        select(QueueUser).where(QueueUser.queue_id == queue_id, QueueUser.user_id == user_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not in this queue")

    entry.status = QueueUserStatus.visiting

    visit = Visit(
        queue_id=queue_id,
        island_id=queue.island_id,
        user_id=user_id,
        entered_at=datetime.now(timezone.utc),
    )
    db.add(visit)
    await db.commit()
    await db.refresh(visit)
    return visit


@router.post("/{visit_id}/end", response_model=VisitResponse)
async def end_visit(
    visit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Host or visitor marks the visit as ended."""
    visit = await db.get(Visit, visit_id)
    if not visit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    if visit.left_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Visit already ended")

    # Allow both the visitor and the host to end the visit
    island = await db.get(Island, visit.island_id)
    if visit.user_id != current_user.id and (not island or island.user_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    visit.left_at = datetime.now(timezone.utc)

    # Update QueueUser status to done
    result = await db.execute(
        select(QueueUser).where(
            QueueUser.queue_id == visit.queue_id,
            QueueUser.user_id == visit.user_id,
            QueueUser.status == QueueUserStatus.visiting,
        )
    )
    entry = result.scalar_one_or_none()
    if entry:
        entry.status = QueueUserStatus.done

    await db.commit()
    await db.refresh(visit)
    return visit


@router.get("/{visit_id}", response_model=VisitResponse)
async def get_visit(visit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    visit = await db.get(Visit, visit_id)
    if not visit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    return visit