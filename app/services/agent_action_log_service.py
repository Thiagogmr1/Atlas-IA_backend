from fastapi import HTTPException, status

from app.models import AgentActionLog, Campaign
from app.models.enums import AgentActionStatus, AgentActionType
from app.repositories.agent_action_log_repository import AgentActionLogRepository
from app.repositories.campaign_repository import CampaignRepository


class AgentActionLogService:
    def __init__(self, logs: AgentActionLogRepository, campaigns: CampaignRepository):
        self.logs = logs
        self.campaigns = campaigns

    def _campaign(self, campaign_id: int, user_id: int) -> Campaign:
        campaign = self.campaigns.get_for_user(campaign_id, user_id)
        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campanha não encontrada",
            )
        return campaign

    def list(
        self,
        campaign_id: int,
        user_id: int,
        action_status: AgentActionStatus | None = None,
        action_type: AgentActionType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentActionLog]:
        self._campaign(campaign_id, user_id)
        return self.logs.list_by_campaign(
            campaign_id, action_status, action_type, limit, offset
        )

    def get(self, campaign_id: int, action_id: int, user_id: int) -> AgentActionLog:
        self._campaign(campaign_id, user_id)
        action = self.logs.get_in_campaign(action_id, campaign_id)
        if action is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ação não encontrada",
            )
        return action

    def approve(self, campaign_id: int, action_id: int, user_id: int) -> AgentActionLog:
        action = self.get(campaign_id, action_id, user_id)

        if action.status != AgentActionStatus.PENDING_APPROVAL:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta ação não está aguardando aprovação",
            )
        if action.approved_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta ação já foi aprovada",
            )
        return self.logs.approve(action, user_id)