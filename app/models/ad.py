from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AdStatus, pg_enum


class Ad(Base):
    __tablename__ = "ad"
    __table_args__ = (UniqueConstraint("campaign_id", "external_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("campaign.id", ondelete="CASCADE"), index=True
    )
    external_id: Mapped[str | None] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(150))
    status: Mapped[AdStatus] = mapped_column(pg_enum(AdStatus, "ad_status"), default=AdStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="ads")
    metrics: Mapped[list["Metric"]] = relationship(
        back_populates="ad", cascade="all, delete-orphan", passive_deletes=True
    )
    action_logs: Mapped[list["AgentActionLog"]] = relationship(back_populates="ad")