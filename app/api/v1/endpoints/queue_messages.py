import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v1.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.island import Island
from app.models.queue import Queue
from app.models.queue_users import QueueUser, QueueUserStatus
from app.models.queue_message import QueueMessage
from app.schemas.queue_message import QueueMessageCreate, QueueMessageResponse

router = APIRouter(tags=["queue messages"])


async def _get_queue_or_404(db: AsyncSession, queue_id: uuid.UUID) -> Queue:
    queue = await db.get(Queue, queue_id)
    if not queue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Queue not found")
    return queue


async def _is_host(db: AsyncSession, queue: Queue, user_id: uuid.UUID) -> bool:
    island = await db.get(Island, queue.island_id)
    return island is not None and island.user_id == user_id


async def _is_participant(db: AsyncSession, queue_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(QueueUser).where(
            QueueUser.queue_id == queue_id,
            QueueUser.user_id == user_id,
            QueueUser.status.in_([QueueUserStatus.waiting, QueueUserStatus.visiting, QueueUserStatus.skipped]),
        )
    )
    return result.scalar_one_or_none() is not None


@router.get("/queues/{queue_id}/messages", response_model=list[QueueMessageResponse])
async def list_messages(queue_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await _get_queue_or_404(db, queue_id)
    result = await db.execute(
        select(QueueMessage)
        .where(QueueMessage.queue_id == queue_id, QueueMessage.is_deleted == False)
        .order_by(QueueMessage.created_at)
    )
    return result.scalars().all()


@router.post("/queues/{queue_id}/messages", response_model=QueueMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    queue_id: uuid.UUID,
    body: QueueMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    queue = await _get_queue_or_404(db, queue_id)

    # Only host and active participants can send messages
    if not await _is_host(db, queue, current_user.id) and not await _is_participant(db, queue_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only host and participants can send messages")

    message = QueueMessage(queue_id=queue_id, sender_id=current_user.id, content=body.content)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


@router.patch("/queue-messages/{message_id}/pin", response_model=QueueMessageResponse)
async def pin_message(
    message_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    message = await db.get(QueueMessage, message_id)
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    queue = await db.get(Queue, message.queue_id)
    if not await _is_host(db, queue, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the host can pin messages")

    message.is_pinned = not message.is_pinned
    await db.commit()
    await db.refresh(message)
    return message


@router.delete("/queue-messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    message = await db.get(QueueMessage, message_id)
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    queue = await db.get(Queue, message.queue_id)
    is_host = await _is_host(db, queue, current_user.id)
    is_own = message.sender_id == current_user.id
    is_mod = current_user.role in (UserRole.admin, UserRole.mod)

    if not (is_host or is_own or is_mod):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    message.is_deleted = True
    message.deleted_by = current_user.id
    await db.commit()