from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.models.enums import CampaignStatus
from app.repositories.ad_account_repository import AdAccountRepository
from app.repositories.campaign_repository import CampaignRepository
from app.routers.deps import get_current_user
from app.schemas.campaign import CampaignCreate, CampaignRead, CampaignUpdate
from app.services.campaign_service import CampaignService

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


def get_service(db: Session = Depends(get_db)) -> CampaignService:
    return CampaignService(CampaignRepository(db), AdAccountRepository(db))


@router.post("", response_model=CampaignRead, status_code=status.HTTP_201_CREATED)
def create_campaign(
    data: CampaignCreate,
    current_user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_service),
):
    return service.create(current_user.id, data)


@router.get("", response_model=list[CampaignRead])
def list_campaigns(
    ad_account_id: int | None = None,
    campaign_status: CampaignStatus | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_service),
):
    return service.list(current_user.id, ad_account_id, campaign_status)


@router.get("/{campaign_id}", response_model=CampaignRead)
def get_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_service),
):
    return service.get(campaign_id, current_user.id)


@router.patch("/{campaign_id}", response_model=CampaignRead)
def update_campaign(
    campaign_id: int,
    data: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_service),
):
    return service.update(campaign_id, current_user.id, data)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_service),
):
    service.delete(campaign_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)