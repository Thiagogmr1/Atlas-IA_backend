from fastapi import HTTPException, status

from app.models import Campaign
from app.models.enums import CampaignStatus
from app.repositories.ad_account_repository import AdAccountRepository
from app.repositories.campaign_repository import CampaignRepository
from app.schemas.campaign import CampaignCreate, CampaignUpdate

# Colunas que não aceitam NULL no banco: no PATCH, não podem ser enviadas como null.
_NOT_NULLABLE = {"name", "status", "autonomy_mode"}


class CampaignService:
    def __init__(self, campaigns: CampaignRepository, accounts: AdAccountRepository):
        self.campaigns = campaigns
        self.accounts = accounts

    def list(
        self,
        user_id: int,
        ad_account_id: int | None = None,
        status: CampaignStatus | None = None,
    ) -> list[Campaign]:
        return self.campaigns.list_by_user(user_id, ad_account_id, status)

    def get(self, campaign_id: int, user_id: int) -> Campaign:
        campaign = self.campaigns.get_for_user(campaign_id, user_id)
        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campanha não encontrada",
            )
        return campaign

    def create(self, user_id: int, data: CampaignCreate) -> Campaign:
        account = self.accounts.get_for_user(data.ad_account_id, user_id)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conta de anúncio não encontrada",
            )
        return self.campaigns.create(**data.model_dump())

    def update(self, campaign_id: int, user_id: int, data: CampaignUpdate) -> Campaign:
        campaign = self.get(campaign_id, user_id)
        fields = data.model_dump(exclude_unset=True)

        for key in _NOT_NULLABLE:
            if key in fields and fields[key] is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"O campo '{key}' não pode ser nulo",
                )

        if not fields:
            return campaign
        return self.campaigns.update(campaign, fields)

    def delete(self, campaign_id: int, user_id: int) -> None:
        campaign = self.get(campaign_id, user_id)
        self.campaigns.delete(campaign)