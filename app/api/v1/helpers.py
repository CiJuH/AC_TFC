import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.strike import Strike
from app.models.ban import Ban
from app.models.user import User

AUTO_BAN_STRIKE_THRESHOLD = 3
AUTO_BAN_WINDOW_DAYS = 7
AUTO_BAN_DURATION_HOURS = 24


async def check_auto_ban(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Create a 24h ban if the user has 3+ strikes in the last 7 days."""
    week_ago = datetime.now(timezone.utc) - timedelta(days=AUTO_BAN_WINDOW_DAYS)
    result = await db.execute(
        select(func.count()).where(
            Strike.user_id == user_id,
            Strike.created_at >= week_ago,
        )
    )
    if result.scalar() < AUTO_BAN_STRIKE_THRESHOLD:
        return

    # Skip if already banned
    result = await db.execute(
        select(Ban).where(Ban.user_id == user_id, Ban.is_active == True)
    )
    if result.scalar_one_or_none():
        return

    now = datetime.now(timezone.utc)
    ban = Ban(
        user_id=user_id,
        banned_by_id=None,
        reason="Automatic ban: 3 strikes in 7 days",
        ban_from=now,
        expires_at=now + timedelta(hours=AUTO_BAN_DURATION_HOURS),
    )
    db.add(ban)

    user = await db.get(User, user_id)
    if user:
        user.is_active = False

    await db.commit()