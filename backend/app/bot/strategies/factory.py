from app.bot.strategies.base import BaseStrategy
from app.bot.strategies.macd import MACDStrategy

_STRATEGIES: dict[str, type[BaseStrategy]] = {
    "macd": MACDStrategy,
}


def create_strategy(name: str, params: dict) -> BaseStrategy:
    cls = _STRATEGIES.get(name)
    if not cls:
        raise ValueError(f"Unknown strategy: {name}")
    return cls(params)
