from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Metric(Base):
    __tablename__ = "metric"
    __table_args__ = (UniqueConstraint("ad_id", "reference_date"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ad_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ad.id", ondelete="CASCADE"), index=True
    )
    reference_date: Mapped[date] = mapped_column(Date)
    spend: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    impressions: Mapped[int] = mapped_column(BigInteger, default=0)
    clicks: Mapped[int] = mapped_column(BigInteger, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    cpa: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    roas: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    ctr: Mapped[Decimal | None] = mapped_column(Numeric(7, 4))

    ad: Mapped["Ad"] = relationship(back_populates="metrics")