from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.base import get_db
from app.models.bot import Bot
from app.models.trade import Trade
from app.models.user import User
from pydantic import BaseModel

router = APIRouter()


class TradeSummary(BaseModel):
    total_pnl: float
    trade_count: int
    win_count: int
    win_rate: float


class DailyPnl(BaseModel):
    date: str
    pnl: float


class RecentTrade(BaseModel):
    id: str
    bot_name: str
    side: str
    symbol: str
    amount: float
    price: float
    pnl: float | None
    executed_at: datetime


class DashboardSummaryResponse(BaseModel):
    summary: TradeSummary
    daily_pnl: list[DailyPnl]
    recent_trades: list[RecentTrade]


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # ユーザーの全ボットIDを取得
    bot_result = await db.execute(select(Bot.id, Bot.name).where(Bot.user_id == current_user.id))
    bot_rows = bot_result.all()
    bot_ids = [r.id for r in bot_rows]
    bot_name_map = {r.id: r.name for r in bot_rows}

    if not bot_ids:
        return DashboardSummaryResponse(
            summary=TradeSummary(total_pnl=0, trade_count=0, win_count=0, win_rate=0),
            daily_pnl=[],
            recent_trades=[],
        )

    # 全体サマリー
    from sqlalchemy import Integer as sa_int
    summary_result = await db.execute(
        select(
            func.coalesce(func.sum(Trade.pnl), 0).label("total_pnl"),
            func.count(Trade.id).label("trade_count"),
            func.coalesce(func.sum(func.cast(Trade.pnl > 0, sa_int)), 0).label("win_count"),
        ).where(Trade.bot_id.in_(bot_ids), Trade.pnl.isnot(None))
    )
    row = summary_result.one()
    win_rate = (row.win_count / row.trade_count * 100) if row.trade_count > 0 else 0.0

    # 日次損益（直近90日）
    daily_result = await db.execute(
        select(
            cast(Trade.executed_at, Date).label("date"),
            func.sum(Trade.pnl).label("pnl"),
        )
        .where(Trade.bot_id.in_(bot_ids), Trade.pnl.isnot(None))
        .group_by(cast(Trade.executed_at, Date))
        .order_by(cast(Trade.executed_at, Date))
        .limit(90)
    )
    daily_pnl = [
        DailyPnl(date=str(r.date), pnl=round(float(r.pnl), 2))
        for r in daily_result.all()
    ]

    # 直近取引履歴（50件）
    trades_result = await db.execute(
        select(Trade)
        .where(Trade.bot_id.in_(bot_ids))
        .order_by(Trade.executed_at.desc())
        .limit(50)
    )
    recent_trades = [
        RecentTrade(
            id=t.id,
            bot_name=bot_name_map.get(t.bot_id, "不明"),
            side=t.side,
            symbol=t.symbol,
            amount=t.amount,
            price=t.price,
            pnl=t.pnl,
            executed_at=t.executed_at,
        )
        for t in trades_result.scalars().all()
    ]

    return DashboardSummaryResponse(
        summary=TradeSummary(
            total_pnl=round(float(row.total_pnl), 2),
            trade_count=row.trade_count,
            win_count=row.win_count or 0,
            win_rate=round(win_rate, 1),
        ),
        daily_pnl=daily_pnl,
        recent_trades=recent_trades,
    )
