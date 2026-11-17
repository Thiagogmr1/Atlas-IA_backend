from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import AgentActionStatus, AgentActionType


class AgentActionLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    ad_id: int | None
    optimization_rule_id: int | None
    action_type: AgentActionType
    status: AgentActionStatus
    triggering_metric: str | None
    measured_value: Decimal | None
    threshold_value: Decimal | None
    justification: str
    approved_by: int | None
    approved_at: datetime | None
    created_at: datetime