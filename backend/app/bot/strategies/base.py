from abc import ABC, abstractmethod

import pandas as pd


class BaseStrategy(ABC):
    def __init__(self, params: dict):
        self.params = params

    @abstractmethod
    def generate_signal(self, ohlcv: list[list]) -> str | None:
        """Returns 'buy', 'sell', or None."""
        ...

    def _to_df(self, ohlcv: list[list]) -> pd.DataFrame:
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["close"] = df["close"].astype(float)
        return df
