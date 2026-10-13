from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Creative
from app.models.enums import CreativeStatus, CreativeType


class CreativeRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_campaign(
        self,
        campaign_id: int,
        creative_status: CreativeStatus | None = None,
        creative_type: CreativeType | None = None,
    ) -> list[Creative]:
        stmt = (
            select(Creative)
            .where(Creative.campaign_id == campaign_id)
            .order_by(Creative.generated_at.desc(), Creative.id.desc())
        )
        if creative_status is not None:
            stmt = stmt.where(Creative.status == creative_status)
        if creative_type is not None:
            stmt = stmt.where(Creative.type == creative_type)
        return list(self.db.scalars(stmt))

    def get_in_campaign(self, creative_id: int, campaign_id: int) -> Creative | None:
        stmt = select(Creative).where(
            Creative.id == creative_id, Creative.campaign_id == campaign_id
        )
        return self.db.scalar(stmt)

    def create(self, campaign_id: int, **fields) -> Creative:
        creative = Creative(campaign_id=campaign_id, **fields)
        self.db.add(creative)
        self.db.commit()
        self.db.refresh(creative)
        return creative

    def set_status(self, creative: Creative, new_status: CreativeStatus) -> Creative:
        creative.status = new_status
        self.db.commit()
        self.db.refresh(creative)
        return creative

    def delete(self, creative: Creative) -> None:
        self.db.delete(creative)
        self.db.commit()