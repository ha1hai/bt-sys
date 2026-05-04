from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.security import decrypt, encrypt
from app.db.base import get_db
from app.models.exchange_key import ExchangeKey
from app.models.user import User
from app.schemas.bot import ExchangeKeyCreate, ExchangeKeyResponse
from app.services.exchanges.factory import create_exchange

router = APIRouter()


@router.get("", response_model=list[ExchangeKeyResponse])
async def list_exchange_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ExchangeKey).where(ExchangeKey.user_id == current_user.id))
    return result.scalars().all()


@router.post("", response_model=ExchangeKeyResponse, status_code=status.HTTP_201_CREATED)
async def add_exchange_key(
    body: ExchangeKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 疎通確認
    try:
        exchange = create_exchange(body.exchange, body.api_key, body.api_secret)
        await exchange.test_connection()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {e}")

    key = ExchangeKey(
        user_id=current_user.id,
        exchange=body.exchange,
        api_key_encrypted=encrypt(body.api_key),
        api_secret_encrypted=encrypt(body.api_secret),
        created_at=datetime.now(timezone.utc),
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)
    return key


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exchange_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ExchangeKey).where(ExchangeKey.id == key_id, ExchangeKey.user_id == current_user.id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    await db.delete(key)
    await db.commit()
