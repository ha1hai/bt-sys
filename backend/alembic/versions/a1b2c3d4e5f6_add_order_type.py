"""add order_type and take_profit_pct to bots

Revision ID: a1b2c3d4e5f6
Revises: ef0778b07f97
Create Date: 2026-05-06

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'ef0778b07f97'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('bots', sa.Column('order_type', sa.String(20), nullable=False, server_default='market'))
    op.add_column('bots', sa.Column('take_profit_pct', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('bots', 'take_profit_pct')
    op.drop_column('bots', 'order_type')
