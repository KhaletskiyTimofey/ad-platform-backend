from typing import Literal

from pydantic import BaseModel, Field

# --- User ---


class UserOut(BaseModel):
    id: str
    role: str
    name: str
    company: str | None = None
    contactName: str | None = None
    email: str | None = None
    telegram: str | None = None
    balance: int


class LoginRequest(BaseModel):
    role: Literal["advertiser", "moderator"]


# --- Creative / Targeting ---


class CreativeIn(BaseModel):
    type: Literal["image", "video", "html"]
    headline: str = Field(min_length=1)
    description: str = Field(min_length=10)
    cta: str
    link: str = Field(pattern=r"^https?://")
    previewUrl: str | None = None
    fileName: str | None = None


class TargetingIn(BaseModel):
    geo: str = ""
    audience: str = Field(min_length=1)
    devices: str = ""


# --- Campaign ---


class CampaignCreate(BaseModel):
    title: str = Field(min_length=1)
    budget: int = Field(ge=1000)
    creative: CreativeIn
    targeting: TargetingIn


class ModerationIn(BaseModel):
    action: Literal["approve", "reject", "changes"]
    comment: str = ""


class OwnerOut(BaseModel):
    id: str
    name: str
    email: str | None = None


class CampaignOut(BaseModel):
    id: str
    ownerId: str
    title: str
    status: str
    budget: int
    spent: int
    impressions: int
    clicks: int
    createdAt: str
    updatedAt: str
    creative: dict
    targeting: dict
    ai: dict
    moderation: dict
    owner: OwnerOut | None = None


# --- Billing ---


class TopupIn(BaseModel):
    amount: int = Field(gt=0)
    method: str = "Банковская карта"


class TransactionOut(BaseModel):
    id: str
    userId: str
    type: str
    amount: int
    method: str | None = None
    title: str
    status: str
    createdAt: str
