import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.models.island import Island, Hemisphere, Fruit
from app.models.queue import Queue, QueueStatus
from app.schemas.island import IslandCreate, IslandUpdate, IslandResponse
from app.schemas.queue import QueueResponse

router = APIRouter(prefix="/islands", tags=["islands"])


@router.get("", response_model=list[IslandResponse])
async def list_islands(
    fruit: Fruit | None = None,
    hemisphere: Hemisphere | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Island).where(Island.deleted_at.is_(None))
    if fruit is not None:
        query = query.where(Island.fruit == fruit)
    if hemisphere is not None:
        query = query.where(Island.hemisphere == hemisphere)
    result = await db.execute(query.order_by(Island.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=IslandResponse, status_code=status.HTTP_201_CREATED)
async def create_island(
    body: IslandCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # One island per user
    result = await db.execute(
        select(Island).where(Island.user_id == current_user.id, Island.deleted_at.is_(None))
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already have an island")

    island = Island(user_id=current_user.id, **body.model_dump())
    db.add(island)
    await db.commit()
    await db.refresh(island)
    return island


@router.get("/me", response_model=IslandResponse)
async def get_my_island(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Island).where(Island.user_id == current_user.id, Island.deleted_at.is_(None))
    )
    island = result.scalar_one_or_none()
    if not island:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You don't have an island")
    return island


@router.get("/{island_id}", response_model=IslandResponse)
async def get_island(island_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    island = await db.get(Island, island_id)
    if not island or island.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Island not found")
    return island


@router.patch("/me", response_model=IslandResponse)
async def update_my_island(
    body: IslandUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Island).where(Island.user_id == current_user.id, Island.deleted_at.is_(None))
    )
    island = result.scalar_one_or_none()
    if not island:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You don't have an island")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(island, field, value)

    await db.commit()
    await db.refresh(island)
    return island


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_island(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Island).where(Island.user_id == current_user.id, Island.deleted_at.is_(None))
    )
    island = result.scalar_one_or_none()
    if not island:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You don't have an island")

    now = datetime.now(timezone.utc)
    island.deleted_at = now

    # Close any open queues belonging to this island
    result = await db.execute(
        select(Queue).where(Queue.island_id == island.id, Queue.closed_at.is_(None))
    )
    for queue in result.scalars().all():
        queue.status = QueueStatus.closed
        queue.closed_at = now

    await db.commit()


@router.get("/{island_id}/active-queue", response_model=QueueResponse)
async def get_island_active_queue(island_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    island = await db.get(Island, island_id)
    if not island or island.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Island not found")

    result = await db.execute(
        select(Queue).where(Queue.island_id == island_id, Queue.closed_at.is_(None))
    )
    queue = result.scalar_one_or_none()
    if not queue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active queue for this island")
    return queue