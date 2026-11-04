from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai import evaluate
from app.auth import get_current_user, require_role
from app.database import get_db
from app.models import Campaign, User
from app.schemas import CampaignCreate, CampaignOut, ModerationIn, OwnerOut

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat() + "Z"


def _to_out(c: Campaign) -> CampaignOut:
    return CampaignOut(
        id=c.id,
        ownerId=c.owner_id,
        title=c.title,
        status=c.status,
        budget=c.budget,
        spent=c.spent,
        impressions=c.impressions,
        clicks=c.clicks,
        createdAt=_iso(c.created_at),
        updatedAt=_iso(c.updated_at),
        creative=c.creative or {},
        targeting=c.targeting or {},
        ai=c.ai or {},
        moderation=c.moderation or {"comment": None, "reviewer": None, "reviewedAt": None},
        owner=OwnerOut(id=c.owner.id, name=c.owner.name, email=c.owner.email) if c.owner else None,
    )


@router.get("", response_model=list[CampaignOut])
async def list_campaigns(
    ownerId: str | None = Query(None),  # noqa: N803
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user: User = Depends(get_current_user),  # noqa: B008
):
    stmt = (
        select(Campaign).options(selectinload(Campaign.owner)).order_by(Campaign.created_at.desc())
    )
    if user.role == "advertiser":
        stmt = stmt.where(Campaign.owner_id == user.id)
    elif ownerId:
        stmt = stmt.where(Campaign.owner_id == ownerId)
    result = await db.execute(stmt)
    return [_to_out(c) for c in result.scalars().all()]


@router.get("/{campaign_id}", response_model=CampaignOut)
async def get_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user: User = Depends(get_current_user),  # noqa: B008
):
    stmt = select(Campaign).options(selectinload(Campaign.owner)).where(Campaign.id == campaign_id)
    c = (await db.execute(stmt)).scalar_one_or_none()
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Кампания не найдена")
    if user.role == "advertiser" and c.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Нет доступа")
    return _to_out(c)


@router.post("", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user: User = Depends(require_role("advertiser")),  # noqa: B008
):
    creative = payload.creative.model_dump()
    ai = evaluate(creative)
    c = Campaign(
        owner_id=user.id,
        title=payload.title,
        status="pending",
        budget=payload.budget,
        creative=creative,
        targeting=payload.targeting.model_dump(),
        ai=ai,
        moderation={"comment": None, "reviewer": None, "reviewedAt": None},
    )
    db.add(c)
    await db.commit()
    await db.refresh(c, ["owner"])
    return _to_out(c)


@router.post("/{campaign_id}/moderation", response_model=CampaignOut)
async def moderate(
    campaign_id: str,
    payload: ModerationIn,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    mod: User = Depends(require_role("moderator")),  # noqa: B008
):
    if payload.action in ("reject", "changes") and not payload.comment.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Комментарий обязателен")
    stmt = select(Campaign).options(selectinload(Campaign.owner)).where(Campaign.id == campaign_id)
    c = (await db.execute(stmt)).scalar_one_or_none()
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Кампания не найдена")
    status_map = {"approve": "approved", "reject": "rejected", "changes": "changes_requested"}
    c.status = status_map[payload.action]
    c.moderation = {
        "comment": payload.comment or None,
        "reviewer": mod.name,
        "reviewedAt": _iso(datetime.utcnow()),
    }
    await db.commit()
    await db.refresh(c, ["owner"])
    return _to_out(c)
