from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AutonomyMode, CampaignStatus


class CampaignCreate(BaseModel):
    ad_account_id: int
    name: str = Field(min_length=1, max_length=150)
    objective: str | None = Field(default=None, max_length=150)
    product: str | None = Field(default=None, max_length=150)
    target_audience: str | None = Field(default=None, max_length=150)
    offer: str | None = Field(default=None, max_length=150)
    budget: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    autonomy_mode: AutonomyMode = AutonomyMode.MANUAL


class CampaignUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    objective: str | None = Field(default=None, max_length=150)
    product: str | None = Field(default=None, max_length=150)
    target_audience: str | None = Field(default=None, max_length=150)
    offer: str | None = Field(default=None, max_length=150)
    budget: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    status: CampaignStatus | None = None
    autonomy_mode: AutonomyMode | None = None


class CampaignRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ad_account_id: int
    external_id: str | None
    name: str
    objective: str | None
    product: str | None
    target_audience: str | None
    offer: str | None
    budget: Decimal | None
    status: CampaignStatus
    autonomy_mode: AutonomyMode
    created_at: datetime