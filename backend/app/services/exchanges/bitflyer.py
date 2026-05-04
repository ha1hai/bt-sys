import ccxt.async_support as ccxt

from app.services.exchanges.base import BaseExchange, Order, Ticker


class BitflyerExchange(BaseExchange):
    def __init__(self, api_key: str, api_secret: str):
        self._client = ccxt.bitflyer({"apiKey": api_key, "secret": api_secret})

    async def test_connection(self) -> None:
        await self._client.fetch_balance()

    async def fetch_ticker(self, symbol: str) -> Ticker:
        t = await self._client.fetch_ticker(symbol)
        return Ticker(symbol=symbol, bid=t["bid"], ask=t["ask"], last=t["last"])

    async def fetch_ohlcv(self, symbol: str, timeframe: str = "1m", limit: int = 100) -> list[list]:
        return await self._client.fetch_ohlcv(symbol, timeframe, limit=limit)

    async def create_order(self, symbol: str, side: str, amount: float) -> Order:
        result = await self._client.create_market_order(symbol, side, amount)
        return Order(
            order_id=result["id"],
            symbol=symbol,
            side=side,
            amount=result["amount"],
            price=result["average"] or result["price"],
        )

    async def fetch_balance(self) -> dict[str, float]:
        balance = await self._client.fetch_balance()
        return {k: v["free"] for k, v in balance["total"].items() if v > 0}

    async def close(self) -> None:
        await self._client.close()
