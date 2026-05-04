from datetime import datetime
from typing import Any

from pydantic import BaseModel


class BotCreate(BaseModel):
    name: str
    exchange: str
    symbol: str
    trade_type: str  # "spot" or "futures"
    strategy: str
    strategy_params: dict[str, Any] = {}
    budget: float
    stop_loss_pct: float = 5.0


class BotUpdate(BaseModel):
    name: str | None = None
    strategy_params: dict[str, Any] | None = None
    budget: float | None = None
    stop_loss_pct: float | None = None


class BotResponse(BaseModel):
    id: str
    name: str
    exchange: str
    symbol: str
    trade_type: str
    strategy: str
    strategy_params: dict[str, Any]
    budget: float
    stop_loss_pct: float
    status: str
    error_message: str | None
    last_executed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class ExchangeKeyCreate(BaseModel):
    exchange: str
    api_key: str
    api_secret: str


class ExchangeKeyResponse(BaseModel):
    id: str
    exchange: str
    created_at: datetime

    class Config:
        from_attributes = True
