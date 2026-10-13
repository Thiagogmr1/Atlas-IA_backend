from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AdAccountStatus, AdPlatform


class AdAccountCreate(BaseModel):
    platform: AdPlatform
    external_account_id: str = Field(min_length=1, max_length=100)
    access_token: str = Field(min_length=1)
    refresh_token: str | None = None
    token_expires_at: datetime | None = None
    granted_scopes: str | None = None


class AdAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: AdPlatform
    external_account_id: str
    token_expires_at: datetime | None
    granted_scopes: str | None
    status: AdAccountStatus
    connected_at: datetime