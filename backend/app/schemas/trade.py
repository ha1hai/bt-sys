from datetime import datetime

from pydantic import BaseModel


class TradeResponse(BaseModel):
    id: str
    bot_id: str
    side: str
    symbol: str
    amount: float
    price: float
    pnl: float | None
    executed_at: datetime

    class Config:
        from_attributes = True


class PerformanceResponse(BaseModel):
    bot_id: str
    total_pnl: float
    trade_count: int
    win_count: int
    win_rate: float
