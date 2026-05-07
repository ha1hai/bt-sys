from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.base import get_db
from app.models.bot import Bot
from app.models.trade import Position, Trade
from app.models.user import User
from app.schemas.bot import BotCreate, BotResponse, BotUpdate
from app.schemas.trade import BacktestResponse, PerformanceResponse, TradeResponse
from app.bot.backtest import run_backtest, DEFAULT_FEE_RATE
from app.services.exchanges.factory import create_public_exchange, backtest_symbol

router = APIRouter()


async def _get_bot_or_404(bot_id: str, user: User, db: AsyncSession) -> Bot:
    result = await db.execute(select(Bot).where(Bot.id == bot_id, Bot.user_id == user.id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="ボットが見つかりません")
    return bot


@router.get("", response_model=list[BotResponse])
async def list_bots(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Bot).where(Bot.user_id == current_user.id))
    return result.scalars().all()


@router.post("", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    body: BotCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot = Bot(**body.model_dump(), user_id=current_user.id, created_at=datetime.now(timezone.utc))
    db.add(bot)
    await db.commit()
    await db.refresh(bot)
    return bot


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_bot_or_404(bot_id, current_user, db)


@router.patch("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: str,
    body: BotUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot = await _get_bot_or_404(bot_id, current_user, db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(bot, field, value)
    await db.commit()
    await db.refresh(bot)
    return bot


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot = await _get_bot_or_404(bot_id, current_user, db)
    if bot.status == "running":
        raise HTTPException(status_code=400, detail="稼働中のボットは削除できません。先に停止してください")
    pos_result = await db.execute(select(Position).where(Position.bot_id == bot_id))
    position = pos_result.scalar_one_or_none()
    if position:
        raise HTTPException(
            status_code=400,
            detail="未決済のポジションがあります。取引所で注文をキャンセル・決済してから削除してください"
        )
    await db.delete(bot)
    await db.commit()


@router.post("/{bot_id}/start", response_model=BotResponse)
async def start_bot(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot = await _get_bot_or_404(bot_id, current_user, db)
    if bot.status == "running":
        raise HTTPException(status_code=400, detail="ボットはすでに稼働中です")
    bot.status = "running"
    bot.error_message = None
    await db.commit()
    await db.refresh(bot)
    return bot


@router.post("/{bot_id}/stop", response_model=BotResponse)
async def stop_bot(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot = await _get_bot_or_404(bot_id, current_user, db)
    bot.status = "stopped"
    await db.commit()
    await db.refresh(bot)

    pos_result = await db.execute(select(Position).where(Position.bot_id == bot_id))
    position = pos_result.scalar_one_or_none()
    response = BotResponse.model_validate(bot)
    if position:
        order_type = getattr(bot, "order_type", "market") or "market"
        if order_type == "ifdoco":
            response.warning = "未決済のポジションがあります。bitFlyer の管理画面で IFDOCO 注文を確認してください"
        else:
            response.warning = "未決済のポジションがあります。取引所で保有ポジションを確認してください"
    return response


@router.get("/{bot_id}/trades", response_model=list[TradeResponse])
async def list_trades(
    bot_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_bot_or_404(bot_id, current_user, db)
    result = await db.execute(
        select(Trade)
        .where(Trade.bot_id == bot_id)
        .order_by(Trade.executed_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{bot_id}/performance", response_model=PerformanceResponse)
async def get_performance(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_bot_or_404(bot_id, current_user, db)
    result = await db.execute(
        select(
            func.coalesce(func.sum(Trade.pnl), 0).label("total_pnl"),
            func.count(Trade.id).label("trade_count"),
            func.sum(func.cast(Trade.pnl > 0, sa_int)).label("win_count"),
        ).where(Trade.bot_id == bot_id, Trade.pnl.isnot(None))
    )
    row = result.one()
    win_rate = (row.win_count / row.trade_count * 100) if row.trade_count > 0 else 0.0
    return PerformanceResponse(
        bot_id=bot_id,
        total_pnl=row.total_pnl,
        trade_count=row.trade_count,
        win_count=row.win_count or 0,
        win_rate=win_rate,
    )


PERIOD_LIMIT = {"1m": 43200, "3m": 43200, "6m": 43200}  # bitFlyer上限に合わせる
PERIOD_TIMEFRAME_LIMIT = {
    "1m": {"1m": 43200, "5m": 8640, "15m": 2880, "1h": 720, "4h": 180, "1d": 30},
    "3m": {"1m": 43200, "5m": 25920, "15m": 8640, "1h": 2160, "4h": 540, "1d": 90},
    "6m": {"1m": 43200, "5m": 43200, "15m": 25920, "1h": 4320, "4h": 1080, "1d": 180},
}


@router.get("/{bot_id}/backtest", response_model=BacktestResponse)
async def backtest_bot(
    bot_id: str,
    period: str = "1m",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if period not in ("1m", "3m", "6m"):
        raise HTTPException(status_code=400, detail="period は 1m / 3m / 6m を指定してください")

    bot = await _get_bot_or_404(bot_id, current_user, db)

    params = bot.strategy_params or {}
    timeframe = params.get("timeframe", "1h")
    limit = PERIOD_TIMEFRAME_LIMIT.get(period, {}).get(timeframe, 500)

    exchange = create_public_exchange(bot.exchange)
    try:
        ohlcv = await exchange.fetch_ohlcv(backtest_symbol(bot.symbol), timeframe, limit=limit)
    finally:
        await exchange.close()

    result = run_backtest(
        ohlcv=ohlcv,
        strategy_name=bot.strategy,
        strategy_params=params,
        budget=bot.budget,
        stop_loss_pct=bot.stop_loss_pct,
    )

    return BacktestResponse(
        trades=[
            {"side": t.side, "price": t.price, "amount": t.amount, "timestamp": t.timestamp, "fee": t.fee, "pnl": t.pnl}
            for t in result.trades
        ],
        equity_curve=result.equity_curve,
        total_pnl=round(result.total_pnl, 2),
        total_fee=round(result.total_fee, 2),
        trade_count=result.trade_count,
        win_count=result.win_count,
        win_rate=round(result.win_rate, 1),
        max_drawdown=round(result.max_drawdown, 2),
        fee_rate=DEFAULT_FEE_RATE,
    )


# SQLAlchemy Integer型のインポート（win_count計算用）
from sqlalchemy import Integer as sa_int
