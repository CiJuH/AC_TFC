"""add_mod_role

Revision ID: fdabbc3d828c
Revises: f5806ecf0da5
Create Date: 2026-04-01 18:17:11.337710

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'fdabbc3d828c'
down_revision: Union[str, None] = 'f5806ecf0da5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'mod'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values directly.
    # Reverting would require recreating the type and migrating existing data.
    pass
