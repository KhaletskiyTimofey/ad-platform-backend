from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_role
from app.database import get_db
from app.models import Campaign, User
from app.schemas import CampaignOut, ModerateRequest
from app.storage import upload_file

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _to_out(c: Campaign) -> CampaignOut:
    return CampaignOut(
        id=c.id,
        title=c.title,
        description=c.description,
        url=c.url,
        budget=c.budget,
        spent=c.spent,
        impressions=c.impressions,
        clicks=c.clicks,
        status=c.status,
        advertiserId=c.advertiser_id,
        advertiserName=c.advertiser.name if c.advertiser else None,
        mediaUrl=c.media_url,
        mediaType=c.media_type,
        moderatorComment=c.moderator_comment,
        createdAt=c.created_at.strftime("%d.%m.%Y %H:%M"),
    )


@router.get("", response_model=list[CampaignOut])
async def list_campaigns(
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user: User = Depends(get_current_user),  # noqa: B008
):
    stmt = select(Campaign).order_by(Campaign.created_at.desc())
    if user.role == "advertiser":
        stmt = stmt.where(Campaign.advertiser_id == user.id)
    if status_filter and status_filter != "all":
        stmt = stmt.where(Campaign.status == status_filter)
    result = await db.execute(stmt)
    campaigns = result.scalars().all()
    # Загружаем advertiser через lazy-load (нужно для _to_out)
    for c in campaigns:
        await db.refresh(c, ["advertiser"])
    return [_to_out(c) for c in campaigns]


@router.get("/{campaign_id}", response_model=CampaignOut)
async def get_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user: User = Depends(get_current_user),  # noqa: B008
):
    c = await db.get(Campaign, campaign_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found")
    if user.role == "advertiser" and c.advertiser_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden")
    await db.refresh(c, ["advertiser"])
    return _to_out(c)


@router.post("", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    title: str = Form(...),
    description: str = Form(""),
    url: str = Form(...),
    budget: int = Form(...),
    media: UploadFile | None = File(None),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user: User = Depends(require_role("advertiser")),  # noqa: B008
):
    media_url = None
    media_type = None
    if media is not None:
        data = await media.read()
        media_url = upload_file(data, media.filename or "file", media.content_type or "")
        media_type = "image" if (media.content_type or "").startswith("image") else "video"

    c = Campaign(
        title=title,
        description=description or None,
        url=url,
        budget=budget,
        advertiser_id=user.id,
        media_url=media_url,
        media_type=media_type,
        status="pending",
    )
    db.add(c)
    await db.commit()
    await db.refresh(c, ["advertiser"])
    return _to_out(c)


@router.put("/{campaign_id}", response_model=CampaignOut)
async def update_campaign(
    campaign_id: str,
    title: str = Form(...),
    description: str = Form(""),
    url: str = Form(...),
    budget: int = Form(...),
    media: UploadFile | None = File(None),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user: User = Depends(require_role("advertiser")),  # noqa: B008
):
    c = await db.get(Campaign, campaign_id)
    if c is None or c.advertiser_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found")
    if c.status != "pending":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only pending campaigns can be edited")

    c.title = title
    c.description = description or None
    c.url = url
    c.budget = budget
    if media is not None:
        data = await media.read()
        c.media_url = upload_file(data, media.filename or "file", media.content_type or "")
        c.media_type = "image" if (media.content_type or "").startswith("image") else "video"
    c.status = "pending"
    c.moderator_comment = None
    await db.commit()
    await db.refresh(c, ["advertiser"])
    return _to_out(c)


@router.post("/{campaign_id}/moderate", response_model=CampaignOut)
async def moderate_campaign(
    campaign_id: str,
    payload: ModerateRequest,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    _: User = Depends(require_role("moderator")),  # noqa: B008
):
    if payload.status not in ("approved", "rejected"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid status")
    c = await db.get(Campaign, campaign_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found")
    c.status = payload.status
    c.moderator_comment = payload.comment or None
    await db.commit()
    await db.refresh(c, ["advertiser"])
    return _to_out(c)
