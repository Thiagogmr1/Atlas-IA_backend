from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AgentActionLog
from app.models.enums import AgentActionStatus, AgentActionType


class AgentActionLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_campaign(
        self,
        campaign_id: int,
        action_status: AgentActionStatus | None = None,
        action_type: AgentActionType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentActionLog]:
        stmt = (
            select(AgentActionLog)
            .where(AgentActionLog.campaign_id == campaign_id)
            .order_by(AgentActionLog.created_at.desc(), AgentActionLog.id.desc())
            .limit(limit)
            .offset(offset)
        )
        if action_status is not None:
            stmt = stmt.where(AgentActionLog.status == action_status)
        if action_type is not None:
            stmt = stmt.where(AgentActionLog.action_type == action_type)
        return list(self.db.scalars(stmt))

    def get_in_campaign(self, action_id: int, campaign_id: int) -> AgentActionLog | None:
        stmt = select(AgentActionLog).where(
            AgentActionLog.id == action_id,
            AgentActionLog.campaign_id == campaign_id,
        )
        return self.db.scalar(stmt)

    def approve(self, action: AgentActionLog, user_id: int) -> AgentActionLog:
        action.approved_by = user_id
        action.approved_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(action)
        return action