from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import RuleAction, RuleMetric, RuleOperator, pg_enum


class OptimizationRule(Base):
    __tablename__ = "optimization_rule"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("campaign.id", ondelete="CASCADE"), index=True
    )
    metric: Mapped[RuleMetric] = mapped_column(pg_enum(RuleMetric, "rule_metric"))
    operator: Mapped[RuleOperator] = mapped_column(pg_enum(RuleOperator, "rule_operator"))
    threshold_value: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    action: Mapped[RuleAction] = mapped_column(pg_enum(RuleAction, "rule_action"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="optimization_rules")
    action_logs: Mapped[list["AgentActionLog"]] = relationship(back_populates="optimization_rule")