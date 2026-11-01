from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Campaign
from app.schemas import StatsOut

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=StatsOut)
async def stats(db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(func.count(Campaign.id))) or 0
    approved = await db.scalar(select(func.count(Campaign.id)).where(Campaign.status == "approved")) or 0
    pending = await db.scalar(select(func.count(Campaign.id)).where(Campaign.status == "pending")) or 0
    rejected = await db.scalar(select(func.count(Campaign.id)).where(Campaign.status == "rejected")) or 0
    impressions = await db.scalar(select(func.coalesce(func.sum(Campaign.impressions), 0))) or 0
    clicks = await db.scalar(select(func.coalesce(func.sum(Campaign.clicks), 0))) or 0
    spent = await db.scalar(select(func.coalesce(func.sum(Campaign.spent), 0))) or 0
    budget = await db.scalar(select(func.coalesce(func.sum(Campaign.budget), 0))) or 0
    return StatsOut(
        campaigns=total,
        approved=approved,
        pending=pending,
        rejected=rejected,
        impressions=impressions,
        clicks=clicks,
        spent=spent,
        budget=budget,
    )


# --- Заготовка для скрипта встраивания (ТЗ, Блок 3.3) ---

@router.get("/serve/{campaign_id}")
async def serve(campaign_id: str, db: AsyncSession = Depends(get_db)):
    c = await db.get(Campaign, campaign_id)
    if c is None or c.status != "approved":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    return {
        "id": c.id,
        "title": c.title,
        "description": c.description,
        "url": c.url,
        "mediaUrl": c.media_url,
        "mediaType": c.media_type,
    }


@router.post("/impression/{campaign_id}")
async def impression(campaign_id: str, db: AsyncSession = Depends(get_db)):
    c = await db.get(Campaign, campaign_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    c.impressions += 1
    # Списание условной стоимости показа (демо)
    if c.spent < c.budget:
        c.spent = min(c.budget, c.spent + 1)
    await db.commit()
    return {"ok": True}


@router.post("/click/{campaign_id}")
async def click(campaign_id: str, db: AsyncSession = Depends(get_db)):
    c = await db.get(Campaign, campaign_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    c.clicks += 1
    if c.spent < c.budget:
        c.spent = min(c.budget, c.spent + 5)
    await db.commit()
    return {"ok": True}