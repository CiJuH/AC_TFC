from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models here so Alembic can detect them
from app.models import (  # noqa: F401, E402
    user,
    island,
    chat,
    private_message,
    queue,
    queue_message,
    queue_users,
    visit,
    review,
    report,
    ban,
    strike,
    friendship,
)