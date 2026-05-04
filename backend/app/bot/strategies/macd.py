import pandas as pd
import pandas_ta as ta

from app.bot.strategies.base import BaseStrategy


class MACDStrategy(BaseStrategy):
    """
    シグナル: MACDラインがシグナルラインを上抜けで buy、下抜けで sell
    params: fast(12), slow(26), signal(9)
    """

    def generate_signal(self, ohlcv: list[list]) -> str | None:
        df = self._to_df(ohlcv)
        fast = self.params.get("fast", 12)
        slow = self.params.get("slow", 26)
        signal = self.params.get("signal", 9)

        macd = ta.macd(df["close"], fast=fast, slow=slow, signal=signal)
        if macd is None or len(macd) < 2:
            return None

        macd_col = f"MACD_{fast}_{slow}_{signal}"
        sig_col = f"MACDs_{fast}_{slow}_{signal}"

        prev_macd = macd[macd_col].iloc[-2]
        prev_sig = macd[sig_col].iloc[-2]
        curr_macd = macd[macd_col].iloc[-1]
        curr_sig = macd[sig_col].iloc[-1]

        if prev_macd <= prev_sig and curr_macd > curr_sig:
            return "buy"
        if prev_macd >= prev_sig and curr_macd < curr_sig:
            return "sell"
        return None
