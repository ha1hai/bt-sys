import ccxt.async_support as ccxt

from app.services.exchanges.base import BaseExchange, Order, Ticker

# bitFlyer の通貨ペア表記変換（ccxt形式 → bitFlyer API形式）
_PRODUCT_CODE: dict[str, str] = {
    "BTC/JPY": "BTC_JPY",
    "ETH/JPY": "ETH_JPY",
    "XRP/JPY": "XRP_JPY",
}


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

    async def send_ifdoco(
        self,
        symbol: str,
        amount: float,
        entry_price: float,
        take_profit_pct: float,
        stop_loss_pct: float,
    ) -> str:
        """
        IFDOCO注文を送信する。
        1発目: 指値買い（maker エントリー）
        2発目: OCO（指値利確 maker + 逆指値損切り taker）
        戻り値: parent_order_acceptance_id
        """
        product_code = _PRODUCT_CODE.get(symbol, symbol.replace("/", "_"))
        take_profit_price = round(entry_price * (1 + take_profit_pct / 100))
        stop_loss_price = round(entry_price * (1 - stop_loss_pct / 100))

        result = await self._client.private_post_sendparentorder({
            "order_method": "IFDOCO",
            "time_in_force": "GTC",
            "parameters": [
                {
                    "product_code": product_code,
                    "condition_type": "LIMIT",
                    "side": "BUY",
                    "price": entry_price,
                    "size": amount,
                },
                {
                    "product_code": product_code,
                    "condition_type": "LIMIT",
                    "side": "SELL",
                    "price": take_profit_price,
                    "size": amount,
                },
                {
                    "product_code": product_code,
                    "condition_type": "STOP",
                    "side": "SELL",
                    "trigger_price": stop_loss_price,
                    "size": amount,
                },
            ],
        })
        return result.get("parent_order_acceptance_id", "")

    async def close(self) -> None:
        await self._client.close()
