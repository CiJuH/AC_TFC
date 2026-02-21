from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models here so Alembic can detect them
from app.models import (  # noqa: F401, E402
    user,
    queue,
    queue_users,
    dodo_code,
    turnip_price,
    visit,
    review,
    chat,
    message,
    report,
    ban,
)
