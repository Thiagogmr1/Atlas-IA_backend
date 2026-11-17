from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.models.enums import CreativeStatus, CreativeType
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.creative_repository import CreativeRepository
from app.routers.deps import get_current_user
from app.schemas.creative import CreativeCreate, CreativeRead, CreativeReview
from app.services.creative_service import CreativeService

router = APIRouter(prefix="/campaigns/{campaign_id}/creatives", tags=["Creatives"])


def get_service(db: Session = Depends(get_db)) -> CreativeService:
    return CreativeService(CreativeRepository(db), CampaignRepository(db))


@router.post("", response_model=CreativeRead, status_code=status.HTTP_201_CREATED)
def create_creative(
    campaign_id: int,
    data: CreativeCreate,
    current_user: User = Depends(get_current_user),
    service: CreativeService = Depends(get_service),
):
    return service.create(campaign_id, current_user.id, data)


@router.get("", response_model=list[CreativeRead])
def list_creatives(
    campaign_id: int,
    creative_status: CreativeStatus | None = Query(default=None, alias="status"),
    creative_type: CreativeType | None = Query(default=None, alias="type"),
    current_user: User = Depends(get_current_user),
    service: CreativeService = Depends(get_service),
):
    return service.list(campaign_id, current_user.id, creative_status, creative_type)


@router.get("/{creative_id}", response_model=CreativeRead)
def get_creative(
    campaign_id: int,
    creative_id: int,
    current_user: User = Depends(get_current_user),
    service: CreativeService = Depends(get_service),
):
    return service.get(campaign_id, creative_id, current_user.id)


@router.patch("/{creative_id}/status", response_model=CreativeRead)
def review_creative(
    campaign_id: int,
    creative_id: int,
    data: CreativeReview,
    current_user: User = Depends(get_current_user),
    service: CreativeService = Depends(get_service),
):
    return service.review(campaign_id, creative_id, current_user.id, data)


@router.delete("/{creative_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_creative(
    campaign_id: int,
    creative_id: int,
    current_user: User = Depends(get_current_user),
    service: CreativeService = Depends(get_service),
):
    service.delete(campaign_id, creative_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)