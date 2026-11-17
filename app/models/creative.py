from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import CreativeStatus, CreativeType, pg_enum


class Creative(Base):
    __tablename__ = "creative"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("campaign.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[CreativeType] = mapped_column(pg_enum(CreativeType, "creative_type"))
    content_url: Mapped[str] = mapped_column(Text)
    status: Mapped[CreativeStatus] = mapped_column(
        pg_enum(CreativeStatus, "creative_status"), default=CreativeStatus.GENERATED
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="creatives")