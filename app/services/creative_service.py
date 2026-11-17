from fastapi import HTTPException, status

from app.models import Campaign, Creative
from app.models.enums import CreativeStatus, CreativeType
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.creative_repository import CreativeRepository
from app.schemas.creative import CreativeCreate, CreativeReview


class CreativeService:
    def __init__(self, creatives: CreativeRepository, campaigns: CampaignRepository):
        self.creatives = creatives
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
        creative_status: CreativeStatus | None = None,
        creative_type: CreativeType | None = None,
    ) -> list[Creative]:
        self._campaign(campaign_id, user_id)
        return self.creatives.list_by_campaign(
            campaign_id, creative_status, creative_type
        )

    def get(self, campaign_id: int, creative_id: int, user_id: int) -> Creative:
        self._campaign(campaign_id, user_id)
        creative = self.creatives.get_in_campaign(creative_id, campaign_id)
        if creative is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Criativo não encontrado",
            )
        return creative

    def create(self, campaign_id: int, user_id: int, data: CreativeCreate) -> Creative:
        self._campaign(campaign_id, user_id)
        return self.creatives.create(campaign_id, **data.model_dump())

    def review(
        self,
        campaign_id: int,
        creative_id: int,
        user_id: int,
        data: CreativeReview,
    ) -> Creative:
        creative = self.get(campaign_id, creative_id, user_id)
        if creative.status != CreativeStatus.GENERATED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este criativo já foi avaliado",
            )
        return self.creatives.set_status(creative, data.status)

    def delete(self, campaign_id: int, creative_id: int, user_id: int) -> None:
        creative = self.get(campaign_id, creative_id, user_id)
        self.creatives.delete(creative)