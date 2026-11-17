from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.optimization_rule_repository import OptimizationRuleRepository
from app.routers.deps import get_current_user
from app.schemas.optimization_rule import (
    OptimizationRuleCreate,
    OptimizationRuleRead,
    OptimizationRuleUpdate,
)
from app.services.optimization_rule_service import OptimizationRuleService

router = APIRouter(
    prefix="/campaigns/{campaign_id}/rules", tags=["Optimization Rules"]
)


def get_service(db: Session = Depends(get_db)) -> OptimizationRuleService:
    return OptimizationRuleService(
        OptimizationRuleRepository(db), CampaignRepository(db)
    )


@router.post("", response_model=OptimizationRuleRead, status_code=status.HTTP_201_CREATED)
def create_rule(
    campaign_id: int,
    data: OptimizationRuleCreate,
    current_user: User = Depends(get_current_user),
    service: OptimizationRuleService = Depends(get_service),
):
    return service.create(campaign_id, current_user.id, data)


@router.get("", response_model=list[OptimizationRuleRead])
def list_rules(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    service: OptimizationRuleService = Depends(get_service),
):
    return service.list(campaign_id, current_user.id)


@router.get("/{rule_id}", response_model=OptimizationRuleRead)
def get_rule(
    campaign_id: int,
    rule_id: int,
    current_user: User = Depends(get_current_user),
    service: OptimizationRuleService = Depends(get_service),
):
    return service.get(campaign_id, rule_id, current_user.id)


@router.patch("/{rule_id}", response_model=OptimizationRuleRead)
def update_rule(
    campaign_id: int,
    rule_id: int,
    data: OptimizationRuleUpdate,
    current_user: User = Depends(get_current_user),
    service: OptimizationRuleService = Depends(get_service),
):
    return service.update(campaign_id, rule_id, current_user.id, data)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(
    campaign_id: int,
    rule_id: int,
    current_user: User = Depends(get_current_user),
    service: OptimizationRuleService = Depends(get_service),
):
    service.delete(campaign_id, rule_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)