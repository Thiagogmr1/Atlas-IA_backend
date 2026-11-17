from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RuleAction, RuleMetric, RuleOperator


class OptimizationRuleCreate(BaseModel):
    metric: RuleMetric
    operator: RuleOperator
    threshold_value: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    action: RuleAction
    is_active: bool = True


class OptimizationRuleUpdate(BaseModel):
    metric: RuleMetric | None = None
    operator: RuleOperator | None = None
    threshold_value: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=2
    )
    action: RuleAction | None = None
    is_active: bool | None = None


class OptimizationRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    metric: RuleMetric
    operator: RuleOperator
    threshold_value: Decimal
    action: RuleAction
    is_active: bool
    created_at: datetime