import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_id: Mapped[str] = mapped_column(String, ForeignKey("bots.id"), nullable=False, index=True)
    exchange_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    side: Mapped[str] = mapped_column(String(10), nullable=False)   # "buy" or "sell"
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    pnl: Mapped[float | None] = mapped_column(Float, nullable=True)  # 決済時に記録
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    bot: Mapped["Bot"] = relationship("Bot", back_populates="trades")


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_id: Mapped[str] = mapped_column(String, ForeignKey("bots.id"), nullable=False, unique=True)
    side: Mapped[str] = mapped_column(String(10), nullable=False)   # "long" or "short"
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    bot: Mapped["Bot"] = relationship("Bot", back_populates="position")
