"""initial

Revision ID: ef0778b07f97
Revises: 
Create Date: 2026-05-05 01:01:07.542294

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef0778b07f97'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "exchange_keys",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("exchange", sa.String(50), nullable=False),
        sa.Column("api_key_encrypted", sa.String(512), nullable=False),
        sa.Column("api_secret_encrypted", sa.String(512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "bots",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("exchange", sa.String(50), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("trade_type", sa.String(10), nullable=False),
        sa.Column("strategy", sa.String(50), nullable=False),
        sa.Column("strategy_params", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("budget", sa.Float(), nullable=False),
        sa.Column("stop_loss_pct", sa.Float(), nullable=False, server_default="5.0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="stopped"),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("last_executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "positions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("bot_id", sa.String(), nullable=False),
        sa.Column("side", sa.String(10), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["bot_id"], ["bots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bot_id"),
    )

    op.create_table(
        "trades",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("bot_id", sa.String(), nullable=False),
        sa.Column("exchange_order_id", sa.String(100), nullable=True),
        sa.Column("side", sa.String(10), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("pnl", sa.Float(), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["bot_id"], ["bots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trades_bot_id", "trades", ["bot_id"])
    op.create_index("ix_trades_executed_at", "trades", ["executed_at"])


def downgrade() -> None:
    op.drop_table("trades")
    op.drop_table("positions")
    op.drop_table("bots")
    op.drop_table("exchange_keys")
    op.drop_index("ix_users_email", "users")
    op.drop_table("users")
