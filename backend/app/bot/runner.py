"""
ボット実行ループ。systemdサービスとして常時起動し、
一定間隔でDBのrunning状態のボットを処理する。
"""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import decrypt
from app.db.base import AsyncSessionLocal
from app.models.bot import Bot
from app.models.trade import Position, Trade
from app.services.exchanges.factory import create_exchange
from app.bot.strategies.factory import create_strategy
from app.services.notifier import notify

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_SECONDS = 60
DEFAULT_TIMEFRAME = "1h"
DEFAULT_OHLCV_LIMIT = 100


async def run_bot(bot: Bot, session) -> None:
    logger.info(f"Running bot {bot.id} ({bot.name})")

    from sqlalchemy import select as sel
    from app.models.exchange_key import ExchangeKey
    result = await session.execute(
        sel(ExchangeKey).where(
            ExchangeKey.user_id == bot.user_id,
            ExchangeKey.exchange == bot.exchange,
        )
    )
    key = result.scalar_one_or_none()
    if not key:
        bot.status = "error"
        bot.error_message = "Exchange key not found"
        return

    # ボットごとの実行設定（strategy_paramsから取得、なければデフォルト）
    params = bot.strategy_params or {}
    timeframe = params.get("timeframe", DEFAULT_TIMEFRAME)
    ohlcv_limit = params.get("ohlcv_limit", DEFAULT_OHLCV_LIMIT)

    exchange = create_exchange(bot.exchange, decrypt(key.api_key_encrypted), decrypt(key.api_secret_encrypted))
    try:
        strategy = create_strategy(bot.strategy, bot.strategy_params)
        ohlcv = await exchange.fetch_ohlcv(bot.symbol, timeframe, limit=ohlcv_limit)
        signal = strategy.generate_signal(ohlcv)

        # ポジション取得
        pos_result = await session.execute(select(Position).where(Position.bot_id == bot.id))
        position = pos_result.scalar_one_or_none()

        ticker = await exchange.fetch_ticker(bot.symbol)
        current_price = ticker.last

        # 成行注文モードのみrunner側でストップロスを管理（IFDOCOはbitFlyer側で管理）
        order_type = getattr(bot, "order_type", "market") or "market"
        if order_type == "market" and position:
            loss_pct = (current_price - position.entry_price) / position.entry_price * 100
            if position.side == "long" and loss_pct <= -bot.stop_loss_pct:
                signal = "sell"
                logger.warning(f"Bot {bot.id}: stop loss triggered")

        if signal == "buy" and not position:
            balance = await exchange.fetch_balance()
            base_currency = bot.symbol.split("/")[1]
            available = min(balance.get(base_currency, 0), bot.budget)
            amount = available / current_price

            if amount > 0:
                order_type = getattr(bot, "order_type", "market") or "market"
                take_profit_pct = getattr(bot, "take_profit_pct", None)

                if order_type == "ifdoco" and take_profit_pct and hasattr(exchange, "send_ifdoco"):
                    # IFDOCO: 成行買い + OCO（利確指値・損切り逆指値）を一括送信
                    acceptance_id = await exchange.send_ifdoco(
                        symbol=bot.symbol,
                        amount=amount,
                        take_profit_pct=take_profit_pct,
                        stop_loss_pct=bot.stop_loss_pct,
                        current_price=current_price,
                    )
                    take_profit_price = round(current_price * (1 + take_profit_pct / 100))
                    stop_loss_price = round(current_price * (1 - bot.stop_loss_pct / 100))
                    session.add(Trade(
                        bot_id=bot.id,
                        exchange_order_id=acceptance_id,
                        side="buy",
                        symbol=bot.symbol,
                        amount=amount,
                        price=current_price,
                        executed_at=datetime.now(timezone.utc),
                    ))
                    session.add(Position(
                        bot_id=bot.id,
                        side="long",
                        amount=amount,
                        entry_price=current_price,
                        opened_at=datetime.now(timezone.utc),
                    ))
                    await notify(
                        bot,
                        f"IFDOCO BUY {bot.symbol} @ {current_price} "
                        f"TP: {take_profit_price} SL: {stop_loss_price}"
                    )
                else:
                    # 成行注文
                    order = await exchange.create_order(bot.symbol, "buy", amount)
                    session.add(Trade(
                        bot_id=bot.id,
                        exchange_order_id=order.order_id,
                        side="buy",
                        symbol=bot.symbol,
                        amount=order.amount,
                        price=order.price,
                        executed_at=datetime.now(timezone.utc),
                    ))
                    session.add(Position(
                        bot_id=bot.id,
                        side="long",
                        amount=order.amount,
                        entry_price=order.price,
                        opened_at=datetime.now(timezone.utc),
                    ))
                    await notify(bot, f"BUY {bot.symbol} @ {order.price}")

        elif signal == "sell" and position:
            order_type = getattr(bot, "order_type", "market") or "market"
            if order_type == "ifdoco":
                # IFDOCO では bitFlyer 側で OCO が管理するため runner からの売り注文は不要
                # ポジションレコードのみ削除してDBを整合させる
                await session.delete(position)
                await notify(bot, f"SELL signal {bot.symbol} (managed by IFDOCO on exchange)")
            else:
                order = await exchange.create_order(bot.symbol, "sell", position.amount)
                pnl = (order.price - position.entry_price) * position.amount
                session.add(Trade(
                    bot_id=bot.id,
                    exchange_order_id=order.order_id,
                    side="sell",
                    symbol=bot.symbol,
                    amount=order.amount,
                    price=order.price,
                    pnl=pnl,
                    executed_at=datetime.now(timezone.utc),
                ))
                await session.delete(position)
                await notify(bot, f"SELL {bot.symbol} @ {order.price} PnL: {pnl:.2f}")

        bot.last_executed_at = datetime.now(timezone.utc)

    except Exception as e:
        logger.error(f"Bot {bot.id} error: {e}")
        bot.status = "error"
        bot.error_message = str(e)[:500]
        await notify(bot, f"ERROR: {e}")
    finally:
        await exchange.close()


async def run_all_bots() -> None:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Bot).where(Bot.status == "running"))
        bots = result.scalars().all()

        for bot in bots:
            # ボットごとの interval_seconds に基づいて実行タイミングを判定
            interval = (bot.strategy_params or {}).get("interval_seconds", DEFAULT_INTERVAL_SECONDS)
            if bot.last_executed_at is not None:
                elapsed = (now - bot.last_executed_at).total_seconds()
                if elapsed < interval:
                    continue
            await run_bot(bot, session)

        await session.commit()


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger.info("Bot runner started")
    # メインループは最小間隔（60秒）で回し、各ボットのinterval_secondsで実行を制御
    while True:
        try:
            await run_all_bots()
        except Exception as e:
            logger.error(f"Runner error: {e}")
        await asyncio.sleep(DEFAULT_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
