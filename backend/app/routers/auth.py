from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_token, get_current_user
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, LoginResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    role = payload.role if payload.role in ("advertiser", "moderator") else "advertiser"
    # Демо-режим: первый пользователь с этой ролью, иначе создаём
    result = await db.execute(select(User).where(User.role == role).limit(1))
    user = result.scalar_one_or_none()
    if user is None:
        name = "Рекламодатель" if role == "advertiser" else "Модератор"
        user = User(name=name, role=role, balance=10000 if role == "advertiser" else 0)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return LoginResponse(token=create_token(user), user=UserOut.model_validate(user))


@router.post("/logout")
async def logout(_: User = Depends(get_current_user)) -> dict:
    # JWT stateless; на клиенте просто удаляется токен
    return {"ok": True}


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)