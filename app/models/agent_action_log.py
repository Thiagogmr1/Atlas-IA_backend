from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AgentActionStatus, AgentActionType, pg_enum


class AgentActionLog(Base):
    __tablename__ = "agent_action_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("campaign.id", ondelete="CASCADE"), index=True
    )
    ad_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("ad.id", ondelete="SET NULL"), index=True
    )
    optimization_rule_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("optimization_rule.id", ondelete="SET NULL"), index=True
    )
    action_type: Mapped[AgentActionType] = mapped_column(
        pg_enum(AgentActionType, "agent_action_type")
    )
    status: Mapped[AgentActionStatus] = mapped_column(
        pg_enum(AgentActionStatus, "agent_action_status")
    )
    triggering_metric: Mapped[str | None] = mapped_column(String(50))
    measured_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    threshold_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    justification: Mapped[str] = mapped_column(Text)
    approved_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("user.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="action_logs")
    ad: Mapped[Optional["Ad"]] = relationship(back_populates="action_logs")
    optimization_rule: Mapped[Optional["OptimizationRule"]] = relationship(
        back_populates="action_logs"
    )
    approver: Mapped[Optional["User"]] = relationship(foreign_keys=[approved_by])