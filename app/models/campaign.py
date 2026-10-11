from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AutonomyMode, CampaignStatus, pg_enum


class Campaign(Base):
    __tablename__ = "campaign"
    __table_args__ = (UniqueConstraint("ad_account_id", "external_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ad_account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ad_account.id", ondelete="CASCADE"), index=True
    )
    external_id: Mapped[str | None] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(150))
    objective: Mapped[str | None] = mapped_column(String(150))
    product: Mapped[str | None] = mapped_column(String(150))
    target_audience: Mapped[str | None] = mapped_column(String(150))
    offer: Mapped[str | None] = mapped_column(String(150))
    budget: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    status: Mapped[CampaignStatus] = mapped_column(
        pg_enum(CampaignStatus, "campaign_status"), default=CampaignStatus.DRAFT
    )
    autonomy_mode: Mapped[AutonomyMode] = mapped_column(
        pg_enum(AutonomyMode, "autonomy_mode"), default=AutonomyMode.MANUAL
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    ad_account: Mapped["AdAccount"] = relationship(back_populates="campaigns")
    optimization_rules: Mapped[list["OptimizationRule"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan", passive_deletes=True
    )
    ads: Mapped[list["Ad"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan", passive_deletes=True
    )
    creatives: Mapped[list["Creative"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan", passive_deletes=True
    )
    action_logs: Mapped[list["AgentActionLog"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan", passive_deletes=True
    )