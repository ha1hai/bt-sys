from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.base import get_db
from app.models.bot import Bot
from app.models.trade import Trade
from app.models.user import User
from app.schemas.bot import BotCreate, BotResponse, BotUpdate
from app.schemas.trade import PerformanceResponse, TradeResponse

router = APIRouter()


async def _get_bot_or_404(bot_id: str, user: User, db: AsyncSession) -> Bot:
    result = await db.execute(select(Bot).where(Bot.id == bot_id, Bot.user_id == user.id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
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
        raise HTTPException(status_code=400, detail="Stop the bot before deleting")
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
        raise HTTPException(status_code=400, detail="Bot is already running")
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
    return bot


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


# SQLAlchemy Integer型のインポート（win_count計算用）
from sqlalchemy import Integer as sa_int
