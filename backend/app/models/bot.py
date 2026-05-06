import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Bot(Base):
    __tablename__ = "bots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    exchange: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)   # e.g. "BTC/JPY"
    trade_type: Mapped[str] = mapped_column(String(10), nullable=False)  # "spot" or "futures"
    strategy: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "macd"
    strategy_params: Mapped[dict] = mapped_column(JSON, default=dict)
    budget: Mapped[float] = mapped_column(Float, nullable=False)
    stop_loss_pct: Mapped[float] = mapped_column(Float, default=5.0)
    order_type: Mapped[str] = mapped_column(String(20), default="market")  # market / ifdoco
    take_profit_pct: Mapped[float | None] = mapped_column(Float, nullable=True)  # 利確%（ifdoco時）
    status: Mapped[str] = mapped_column(String(20), default="stopped")  # running / stopped / error
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="bots")
    trades: Mapped[list["Trade"]] = relationship("Trade", back_populates="bot", cascade="all, delete-orphan")
    position: Mapped["Position | None"] = relationship("Position", back_populates="bot", uselist=False, cascade="all, delete-orphan")
