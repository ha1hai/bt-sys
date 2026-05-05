"""
バックテストエンジン。過去OHLCVデータに対して戦略をシミュレーションする。
実際の注文は発生しない。
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.bot.strategies.factory import create_strategy


@dataclass
class BacktestTrade:
    side: str
    price: float
    amount: float
    timestamp: int
    pnl: float | None = None


@dataclass
class BacktestResult:
    trades: list[BacktestTrade] = field(default_factory=list)
    equity_curve: list[dict] = field(default_factory=list)  # [{timestamp, equity}]
    total_pnl: float = 0.0
    trade_count: int = 0
    win_count: int = 0
    win_rate: float = 0.0
    max_drawdown: float = 0.0


def run_backtest(
    ohlcv: list[list],
    strategy_name: str,
    strategy_params: dict,
    budget: float,
    stop_loss_pct: float,
) -> BacktestResult:
    strategy = create_strategy(strategy_name, strategy_params)
    result = BacktestResult()

    position_price: float | None = None
    position_amount: float | None = None
    equity = budget
    peak_equity = budget

    # OHLCVは [timestamp, open, high, low, close, volume]
    # 最低でも slow+signal 本必要。スライディングウィンドウで逐次シグナル判定
    min_bars = max(strategy_params.get("slow", 26) + strategy_params.get("signal", 9), 30)

    for i in range(min_bars, len(ohlcv)):
        window = ohlcv[:i + 1]
        candle = ohlcv[i]
        ts = candle[0]
        close = float(candle[4])

        signal = strategy.generate_signal(window)

        # ストップロスチェック
        if position_price is not None and position_amount is not None:
            loss_pct = (close - position_price) / position_price * 100
            if loss_pct <= -stop_loss_pct:
                signal = "sell"

        if signal == "buy" and position_price is None:
            position_amount = equity / close
            position_price = close
            result.trades.append(BacktestTrade(side="buy", price=close, amount=position_amount, timestamp=ts))

        elif signal == "sell" and position_price is not None and position_amount is not None:
            pnl = (close - position_price) * position_amount
            equity += pnl
            result.trades.append(BacktestTrade(
                side="sell", price=close, amount=position_amount, timestamp=ts, pnl=pnl
            ))
            result.total_pnl += pnl
            result.trade_count += 1
            if pnl > 0:
                result.win_count += 1
            position_price = None
            position_amount = None

        # 含み損益を含む現在の資産評価
        current_equity = equity
        if position_price is not None and position_amount is not None:
            current_equity = equity + (close - position_price) * position_amount

        peak_equity = max(peak_equity, current_equity)
        drawdown = (peak_equity - current_equity) / peak_equity * 100 if peak_equity > 0 else 0
        result.max_drawdown = max(result.max_drawdown, drawdown)

        result.equity_curve.append({"timestamp": ts, "equity": round(current_equity, 2)})

    if result.trade_count > 0:
        result.win_rate = result.win_count / result.trade_count * 100

    return result
