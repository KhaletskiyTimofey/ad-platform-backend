from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    COOKIE_NAME,
    create_session,
    get_optional_user,
)
from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_user_out(u: User) -> UserOut:
    return UserOut(
        id=u.id,
        role=u.role,
        name=u.name,
        company=u.company,
        contactName=u.contact_name,
        email=u.email,
        telegram=u.telegram,
        balance=u.balance,
    )


@router.get("/session", response_model=UserOut | None)
async def session(user: User | None = Depends(get_optional_user)):  # noqa: B008
    return _to_user_out(user) if user else None


@router.post("/oauth/google", response_model=UserOut)
async def oauth_google(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    role = payload.role
    result = await db.execute(select(User).where(User.role == role).limit(1))
    user = result.scalar_one_or_none()
    if user is None:
        name = "Пиксель Студио" if role == "advertiser" else "Модератор AdPulse"
        user = User(
            role=role,
            name=name,
            company="ООО «Пиксель Студио»" if role == "advertiser" else None,
            contact_name="Игорь Ветров" if role == "advertiser" else None,
            email="ads@pixel.studio" if role == "advertiser" else "moderator@adpulse.ru",
            telegram="@pixel_studio" if role == "advertiser" else None,
            balance=12400 if role == "advertiser" else 0,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    token = await create_session(db, user)
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        max_age=settings.SESSION_TTL_DAYS * 24 * 3600,
        path="/",
    )
    return _to_user_out(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user: User | None = Depends(get_optional_user),  # noqa: B008
):
    # простая реализация: удаляем все сессии пользователя, если он известен
    if user is not None:
        from sqlalchemy import delete

        from app.models import Session as SessionModel

        await db.execute(delete(SessionModel).where(SessionModel.user_id == user.id))
        await db.commit()
    response.delete_cookie(COOKIE_NAME, path="/")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
