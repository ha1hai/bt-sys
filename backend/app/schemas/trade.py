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


class BacktestTradeResponse(BaseModel):
    side: str
    price: float
    amount: float
    timestamp: int
    fee: float
    pnl: float | None


class BacktestResponse(BaseModel):
    trades: list[BacktestTradeResponse]
    equity_curve: list[dict]
    total_pnl: float
    total_fee: float
    trade_count: int
    win_count: int
    win_rate: float
    max_drawdown: float
    fee_rate: float
