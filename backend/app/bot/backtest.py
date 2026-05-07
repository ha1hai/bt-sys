"""
バックテストエンジン。過去OHLCVデータに対して戦略をシミュレーションする。
実際の注文は発生しない。

手数料：bitFlyer Lightning 現物
  直近30日取引量10万円未満のデフォルト 0.15%（買い・売り各々に適用）
  1往復のコスト ≒ 0.30%
"""
from dataclasses import dataclass, field

from app.bot.strategies.factory import create_strategy

# bitFlyer Lightning 現物の手数料（直近30日取引量10万円未満のデフォルト）
DEFAULT_FEE_RATE = 0.0015  # 0.15%


@dataclass
class BacktestTrade:
    side: str
    price: float
    amount: float
    timestamp: int
    fee: float = 0.0
    pnl: float | None = None


@dataclass
class BacktestResult:
    trades: list[BacktestTrade] = field(default_factory=list)
    equity_curve: list[dict] = field(default_factory=list)  # [{timestamp, equity}]
    total_pnl: float = 0.0
    total_fee: float = 0.0
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
    fee_rate: float = DEFAULT_FEE_RATE,
) -> BacktestResult:
    strategy = create_strategy(strategy_name, strategy_params)
    result = BacktestResult()

    position_price: float | None = None
    position_amount: float | None = None
    equity = budget
    peak_equity = budget

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
            # 買い手数料を差し引いた後の実効購入数量
            buy_fee = equity * fee_rate
            equity_after_fee = equity - buy_fee
            position_amount = equity_after_fee / close
            position_price = close
            result.total_fee += buy_fee
            result.trades.append(BacktestTrade(
                side="buy", price=close, amount=position_amount, timestamp=ts, fee=buy_fee
            ))

        elif signal == "sell" and position_price is not None and position_amount is not None:
            sell_value = close * position_amount
            sell_fee = sell_value * fee_rate
            net_sell_value = sell_value - sell_fee
            pnl = net_sell_value - (position_price * position_amount)
            equity = position_price * position_amount + pnl  # 元本 + 純損益
            result.total_fee += sell_fee
            result.trades.append(BacktestTrade(
                side="sell", price=close, amount=position_amount, timestamp=ts, fee=sell_fee, pnl=pnl
            ))
            result.total_pnl += pnl
            result.trade_count += 1
            if pnl > 0:
                result.win_count += 1
            position_price = None
            position_amount = None

        # 含み損益を含む現在の資産評価（含み益には手数料未控除）
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
