from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Ticker:
    symbol: str
    bid: float
    ask: float
    last: float


@dataclass
class Order:
    order_id: str
    symbol: str
    side: str
    amount: float
    price: float


class BaseExchange(ABC):
    @abstractmethod
    async def test_connection(self) -> None: ...

    @abstractmethod
    async def fetch_ticker(self, symbol: str) -> Ticker: ...

    @abstractmethod
    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> list[list]: ...

    @abstractmethod
    async def create_order(self, symbol: str, side: str, amount: float) -> Order: ...

    @abstractmethod
    async def fetch_balance(self) -> dict[str, float]: ...
