from app.services.exchanges.base import BaseExchange
from app.services.exchanges.bitflyer import BitflyerExchange
from app.services.exchanges.binance_public import BinancePublicExchange

_EXCHANGES: dict[str, type[BaseExchange]] = {
    "bitflyer": BitflyerExchange,
}

# バックテスト用OHLCVシンボルのマッピング（bitFlyer → Binance）
_BACKTEST_SYMBOL_MAP: dict[str, str] = {
    "BTC/JPY": "BTC/USDT",
    "ETH/JPY": "ETH/USDT",
    "XRP/JPY": "XRP/USDT",
}


def create_exchange(exchange: str, api_key: str, api_secret: str) -> BaseExchange:
    cls = _EXCHANGES.get(exchange)
    if not cls:
        raise ValueError(f"Unsupported exchange: {exchange}")
    return cls(api_key, api_secret)


def create_public_exchange(exchange: str) -> BinancePublicExchange:
    return BinancePublicExchange()


def backtest_symbol(symbol: str) -> str:
    return _BACKTEST_SYMBOL_MAP.get(symbol, symbol)
