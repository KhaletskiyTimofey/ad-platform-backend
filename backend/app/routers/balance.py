from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_role
from app.database import get_db
from app.models import User
from app.schemas import TopupRequest, TopupResponse

router = APIRouter(prefix="/balance", tags=["balance"])


@router.post("/topup", response_model=TopupResponse)
async def topup(
    payload: TopupRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("advertiser")),
):
    if payload.amount <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Amount must be positive")
    user.balance += payload.amount
    await db.commit()
    await db.refresh(user)
    return TopupResponse(balance=user.balance)