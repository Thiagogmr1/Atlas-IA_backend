from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AdAccount, Campaign
from app.models.enums import CampaignStatus


class CampaignRepository:
    def __init__(self, db: Session):
        self.db = db

    def _owned_by(self, user_id: int):
        """Base da consulta: só campanhas de contas que pertencem ao usuário."""
        return (
            select(Campaign)
            .join(AdAccount, Campaign.ad_account_id == AdAccount.id)
            .where(AdAccount.user_id == user_id)
        )

    def list_by_user(
        self,
        user_id: int,
        ad_account_id: int | None = None,
        status: CampaignStatus | None = None,
    ) -> list[Campaign]:
        stmt = self._owned_by(user_id).order_by(Campaign.created_at.desc())
        if ad_account_id is not None:
            stmt = stmt.where(Campaign.ad_account_id == ad_account_id)
        if status is not None:
            stmt = stmt.where(Campaign.status == status)
        return list(self.db.scalars(stmt))

    def get_for_user(self, campaign_id: int, user_id: int) -> Campaign | None:
        stmt = self._owned_by(user_id).where(Campaign.id == campaign_id)
        return self.db.scalar(stmt)

    def create(self, **fields) -> Campaign:
        campaign = Campaign(**fields)
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        return campaign

    def update(self, campaign: Campaign, fields: dict) -> Campaign:
        for key, value in fields.items():
            setattr(campaign, key, value)
        self.db.commit()
        self.db.refresh(campaign)
        return campaign

    def delete(self, campaign: Campaign) -> None:
        self.db.delete(campaign)
        self.db.commit()