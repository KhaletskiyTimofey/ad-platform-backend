from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    role: str  # advertiser / moderator


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    role: str
    balance: int


class LoginResponse(BaseModel):
    token: str
    user: UserOut


class CampaignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str | None = None
    url: str
    budget: int
    spent: int
    impressions: int
    clicks: int
    status: str
    advertiserId: str
    advertiserName: str | None = None
    mediaUrl: str | None = None
    mediaType: str | None = None
    moderatorComment: str | None = None
    createdAt: str


class ModerateRequest(BaseModel):
    status: str  # approved / rejected
    comment: str = ""


class TopupRequest(BaseModel):
    amount: int


class TopupResponse(BaseModel):
    balance: int


class StatsOut(BaseModel):
    campaigns: int
    approved: int
    pending: int
    rejected: int
    impressions: int
    clicks: int
    spent: int
    budget: int
