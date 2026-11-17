from fastapi import HTTPException, status

from app.models import Campaign, OptimizationRule
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.optimization_rule_repository import OptimizationRuleRepository
from app.schemas.optimization_rule import OptimizationRuleCreate, OptimizationRuleUpdate


class OptimizationRuleService:
    def __init__(self, rules: OptimizationRuleRepository, campaigns: CampaignRepository):
        self.rules = rules
        self.campaigns = campaigns

    def _campaign(self, campaign_id: int, user_id: int) -> Campaign:
        campaign = self.campaigns.get_for_user(campaign_id, user_id)
        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campanha não encontrada",
            )
        return campaign

    def list(self, campaign_id: int, user_id: int) -> list[OptimizationRule]:
        self._campaign(campaign_id, user_id)
        return self.rules.list_by_campaign(campaign_id)

    def get(self, campaign_id: int, rule_id: int, user_id: int) -> OptimizationRule:
        self._campaign(campaign_id, user_id)
        rule = self.rules.get_in_campaign(rule_id, campaign_id)
        if rule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Regra de otimização não encontrada",
            )
        return rule

    def create(
        self, campaign_id: int, user_id: int, data: OptimizationRuleCreate
    ) -> OptimizationRule:
        self._campaign(campaign_id, user_id)
        return self.rules.create(campaign_id, **data.model_dump())

    def update(
        self,
        campaign_id: int,
        rule_id: int,
        user_id: int,
        data: OptimizationRuleUpdate,
    ) -> OptimizationRule:
        rule = self.get(campaign_id, rule_id, user_id)
        fields = data.model_dump(exclude_unset=True)

        for key, value in fields.items():
            if value is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"O campo '{key}' não pode ser nulo",
                )

        if not fields:
            return rule
        return self.rules.update(rule, fields)

    def delete(self, campaign_id: int, rule_id: int, user_id: int) -> None:
        rule = self.get(campaign_id, rule_id, user_id)
        self.rules.delete(rule)