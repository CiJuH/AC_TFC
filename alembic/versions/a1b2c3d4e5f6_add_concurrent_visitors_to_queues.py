"""add concurrent_visitors to queues

Revision ID: a1b2c3d4e5f6
Revises: 589de32e1e4c
Create Date: 2026-04-25

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '589de32e1e4c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'queues',
        sa.Column('concurrent_visitors', sa.Integer(), nullable=False, server_default='4')
    )


def downgrade() -> None:
    op.drop_column('queues', 'concurrent_visitors')