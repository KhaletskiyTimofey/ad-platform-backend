import secrets
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Session as SessionModel
from app.models import User

COOKIE_NAME = "adpulse_session"


async def create_session(db: AsyncSession, user: User) -> str:
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(days=settings.SESSION_TTL_DAYS)
    db.add(SessionModel(token=token, user_id=user.id, expires_at=expires))
    await db.commit()
    return token


async def destroy_session(db: AsyncSession, token: str) -> None:
    s = await db.get(SessionModel, token)
    if s:
        await db.delete(s)
        await db.commit()


async def get_optional_user(request: Request, db: AsyncSession = Depends(get_db)) -> User | None:  # noqa: B008
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    s = await db.get(SessionModel, token)
    if s is None or s.expires_at < datetime.utcnow():
        return None
    return await db.get(User, s.user_id)


async def get_current_user(user: User | None = Depends(get_optional_user)) -> User:  # noqa: B008
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Требуется авторизация")
    return user


def require_role(*roles: str):
    async def checker(user: User = Depends(get_current_user)) -> User:  # noqa: B008
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Недостаточно прав")
        return user

    return checker
