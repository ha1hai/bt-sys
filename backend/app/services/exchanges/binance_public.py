import ccxt.async_support as ccxt

from app.services.exchanges.base import BaseExchange, Order, Ticker


class BinancePublicExchange(BaseExchange):
    """バックテスト用。認証不要の公開APIのみ使用。"""

    def __init__(self) -> None:
        self._client = ccxt.binance()

    async def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> list[list]:
        return await self._client.fetch_ohlcv(symbol, timeframe, limit=limit)

    async def close(self) -> None:
        await self._client.close()

    async def test_connection(self) -> None:
        raise NotImplementedError

    async def fetch_ticker(self, symbol: str) -> Ticker:
        raise NotImplementedError

    async def create_order(self, symbol: str, side: str, amount: float) -> Order:
        raise NotImplementedError

    async def fetch_balance(self) -> dict[str, float]:
        raise NotImplementedError
