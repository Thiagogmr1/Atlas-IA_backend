from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import OptimizationRule


class OptimizationRuleRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_campaign(self, campaign_id: int) -> list[OptimizationRule]:
        stmt = (
            select(OptimizationRule)
            .where(OptimizationRule.campaign_id == campaign_id)
            .order_by(OptimizationRule.created_at, OptimizationRule.id)
        )
        return list(self.db.scalars(stmt))

    def get_in_campaign(self, rule_id: int, campaign_id: int) -> OptimizationRule | None:
        stmt = select(OptimizationRule).where(
            OptimizationRule.id == rule_id,
            OptimizationRule.campaign_id == campaign_id,
        )
        return self.db.scalar(stmt)

    def create(self, campaign_id: int, **fields) -> OptimizationRule:
        rule = OptimizationRule(campaign_id=campaign_id, **fields)
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def update(self, rule: OptimizationRule, fields: dict) -> OptimizationRule:
        for key, value in fields.items():
            setattr(rule, key, value)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete(self, rule: OptimizationRule) -> None:
        self.db.delete(rule)
        self.db.commit()