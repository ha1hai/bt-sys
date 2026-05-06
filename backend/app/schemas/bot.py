from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class StrategyParams(BaseModel):
    """
    全戦略共通パラメータ + 戦略固有パラメータをまとめたスキーマ。
    strategy_params フィールドとしてボットに保存される。

    共通:
      interval_seconds: ボット実行間隔（秒）。デフォルト60。最小60。
      timeframe:        OHLCVのタイムフレーム。デフォルト"1h"。
      ohlcv_limit:      取得するOHLCV本数。デフォルト100。

    MACD戦略固有:
      fast:   短期EMA期間。デフォルト12。
      slow:   長期EMA期間。デフォルト26。
      signal: シグナル線期間。デフォルト9。
    """
    # 共通
    interval_seconds: int = Field(default=60, ge=60, description="実行間隔（秒）")
    timeframe: str = Field(default="1h", description="OHLCVタイムフレーム (1m/5m/15m/1h/4h/1d)")
    ohlcv_limit: int = Field(default=100, ge=10, le=500, description="OHLCV取得本数")

    # MACD
    fast: int = Field(default=12, ge=2, description="MACD短期EMA期間")
    slow: int = Field(default=26, ge=2, description="MACD長期EMA期間")
    signal: int = Field(default=9, ge=2, description="MACDシグナル線期間")

    class Config:
        extra = "allow"  # 将来の戦略パラメータ追加に対応


class BotCreate(BaseModel):
    name: str
    exchange: str
    symbol: str
    trade_type: str  # "spot" or "futures"
    strategy: str
    strategy_params: dict[str, Any] = Field(default_factory=dict)
    budget: float
    stop_loss_pct: float = 5.0
    order_type: str = "market"  # market / ifdoco
    take_profit_pct: float | None = None


class BotUpdate(BaseModel):
    name: str | None = None
    strategy_params: dict[str, Any] | None = None
    budget: float | None = None
    stop_loss_pct: float | None = None
    order_type: str | None = None
    take_profit_pct: float | None = None


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
    order_type: str
    take_profit_pct: float | None
    status: str
    error_message: str | None
    last_executed_at: datetime | None
    created_at: datetime
    warning: str | None = None

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
