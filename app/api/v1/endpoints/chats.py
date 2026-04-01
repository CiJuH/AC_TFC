import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.models.chat import Chat
from app.models.private_message import PrivateMessage
from app.schemas.chat import ChatResponse
from app.schemas.private_message import PrivateMessageCreate, PrivateMessageResponse

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=list[ChatResponse])
async def list_chats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Chat)
        .where(or_(Chat.user_a_id == current_user.id, Chat.user_b_id == current_user.id))
        .order_by(Chat.last_message_at.desc().nullslast())
    )
    return result.scalars().all()


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def get_or_create_chat(
    friend_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if friend_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot chat with yourself")

    friend = await db.get(User, friend_id)
    if not friend or not friend.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Normalize order so (A,B) and (B,A) map to the same chat
    a, b = sorted([current_user.id, friend_id])
    result = await db.execute(
        select(Chat).where(Chat.user_a_id == a, Chat.user_b_id == b)
    )
    chat = result.scalar_one_or_none()

    if not chat:
        chat = Chat(user_a_id=a, user_b_id=b)
        db.add(chat)
        await db.commit()
        await db.refresh(chat)

    return chat


@router.get("/{chat_id}/messages", response_model=list[PrivateMessageResponse])
async def list_messages(
    chat_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = await db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    if current_user.id not in (chat.user_a_id, chat.user_b_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your chat")

    result = await db.execute(
        select(PrivateMessage)
        .where(PrivateMessage.chat_id == chat_id, PrivateMessage.is_deleted == False)
        .order_by(PrivateMessage.created_at)
    )
    return result.scalars().all()


@router.post("/{chat_id}/messages", response_model=PrivateMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    chat_id: uuid.UUID,
    body: PrivateMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = await db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    if current_user.id not in (chat.user_a_id, chat.user_b_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your chat")

    from datetime import datetime, timezone
    message = PrivateMessage(chat_id=chat_id, sender_id=current_user.id, content=body.content)
    db.add(message)
    chat.last_message_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(message)
    return message


@router.patch("/{chat_id}/messages/{message_id}/read", response_model=PrivateMessageResponse)
async def mark_as_read(
    chat_id: uuid.UUID,
    message_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    message = await db.get(PrivateMessage, message_id)
    if not message or message.chat_id != chat_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    chat = await db.get(Chat, chat_id)
    if current_user.id not in (chat.user_a_id, chat.user_b_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your chat")

    # Only the receiver can mark as read
    if message.sender_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot mark your own message as read")

    message.is_read = True
    await db.commit()
    await db.refresh(message)
    return message