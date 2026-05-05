from app.services.exchanges.base import BaseExchange
from app.services.exchanges.bitflyer import BitflyerExchange

_EXCHANGES: dict[str, type[BaseExchange]] = {
    "bitflyer": BitflyerExchange,
}


def create_exchange(exchange: str, api_key: str, api_secret: str) -> BaseExchange:
    cls = _EXCHANGES.get(exchange)
    if not cls:
        raise ValueError(f"Unsupported exchange: {exchange}")
    return cls(api_key, api_secret)


def create_public_exchange(exchange: str) -> BaseExchange:
    cls = _EXCHANGES.get(exchange)
    if not cls:
        raise ValueError(f"Unsupported exchange: {exchange}")
    return cls("", "")
