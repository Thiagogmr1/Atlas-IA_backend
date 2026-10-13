from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.models.enums import AgentActionStatus, AgentActionType
from app.repositories.agent_action_log_repository import AgentActionLogRepository
from app.repositories.campaign_repository import CampaignRepository
from app.routers.deps import get_current_user
from app.schemas.agent_action_log import AgentActionLogRead
from app.services.agent_action_log_service import AgentActionLogService

router = APIRouter(prefix="/campaigns/{campaign_id}/actions", tags=["Agent Actions"])


def get_service(db: Session = Depends(get_db)) -> AgentActionLogService:
    return AgentActionLogService(AgentActionLogRepository(db), CampaignRepository(db))


@router.get("", response_model=list[AgentActionLogRead])
def list_actions(
    campaign_id: int,
    action_status: AgentActionStatus | None = Query(default=None, alias="status"),
    action_type: AgentActionType | None = Query(default=None, alias="type"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    service: AgentActionLogService = Depends(get_service),
):
    return service.list(
        campaign_id, current_user.id, action_status, action_type, limit, offset
    )


@router.get("/{action_id}", response_model=AgentActionLogRead)
def get_action(
    campaign_id: int,
    action_id: int,
    current_user: User = Depends(get_current_user),
    service: AgentActionLogService = Depends(get_service),
):
    return service.get(campaign_id, action_id, current_user.id)


@router.post("/{action_id}/approve", response_model=AgentActionLogRead)
def approve_action(
    campaign_id: int,
    action_id: int,
    current_user: User = Depends(get_current_user),
    service: AgentActionLogService = Depends(get_service),
):
    return service.approve(campaign_id, action_id, current_user.id)