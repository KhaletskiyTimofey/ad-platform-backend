from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_role
from app.database import get_db
from app.models import Transaction, User
from app.schemas import TopupIn, TransactionOut, UserOut

router = APIRouter(prefix="/billing", tags=["billing"])


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat() + "Z"


@router.post("/topup", response_model=UserOut)
async def topup(
    payload: TopupIn,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user: User = Depends(require_role("advertiser")),  # noqa: B008
):
    user.balance += payload.amount
    db.add(
        Transaction(
            user_id=user.id,
            type="topup",
            amount=payload.amount,
            method=payload.method,
            title="Пополнение баланса",
            status="success",
        )
    )
    await db.commit()
    await db.refresh(user)
    return UserOut(
        id=user.id,
        role=user.role,
        name=user.name,
        company=user.company,
        contactName=user.contact_name,
        email=user.email,
        telegram=user.telegram,
        balance=user.balance,
    )


@router.get("/transactions", response_model=list[TransactionOut])
async def transactions(
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user: User = Depends(get_current_user),  # noqa: B008
):
    stmt = (
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
    )
    result = await db.execute(stmt)
    return [
        TransactionOut(
            id=t.id,
            userId=t.user_id,
            type=t.type,
            amount=t.amount,
            method=t.method,
            title=t.title,
            status=t.status,
            createdAt=_iso(t.created_at),
        )
        for t in result.scalars().all()
    ]
