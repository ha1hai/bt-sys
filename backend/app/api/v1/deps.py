from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.security import decode_access_token, hash_password
from app.db.base import get_db
from app.models.user import User

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if settings.dev_mode and (credentials is None or credentials.credentials == "dev-token"):
        result = await db.execute(select(User).where(User.email == settings.dev_user_email))
        user = result.scalar_one_or_none()
        if not user:
            user = User(email=settings.dev_user_email, hashed_password=hash_password("dev"), is_active=True)
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        user_id = decode_access_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
