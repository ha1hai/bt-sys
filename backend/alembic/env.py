import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# モデルをすべてインポートしてautogenerateを有効化
from app.db.base import Base
from app.models.user import User
from app.models.exchange_key import ExchangeKey
from app.models.bot import Bot
from app.models.trade import Trade, Position

target_metadata = Base.metadata

# .envのDATABASE_URLをasyncpg→psycopg2に変換（マイグレーション用）
def get_url():
    url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    return url.replace("postgresql+asyncpg://", "postgresql://")


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode() or os.getenv("ALEMBIC_OFFLINE"):
    run_migrations_offline()
else:
    run_migrations_online()
