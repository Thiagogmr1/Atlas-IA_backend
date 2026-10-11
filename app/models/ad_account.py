from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AdAccountStatus, AdPlatform, pg_enum


class AdAccount(Base):
    __tablename__ = "ad_account"
    __table_args__ = (UniqueConstraint("user_id", "platform", "external_account_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user.id", ondelete="CASCADE"), index=True
    )
    platform: Mapped[AdPlatform] = mapped_column(pg_enum(AdPlatform, "ad_platform"))
    external_account_id: Mapped[str] = mapped_column(String(100))
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    granted_scopes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[AdAccountStatus] = mapped_column(
        pg_enum(AdAccountStatus, "ad_account_status"), default=AdAccountStatus.ACTIVE
    )
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="ad_accounts")
    campaigns: Mapped[list["Campaign"]] = relationship(
        back_populates="ad_account", cascade="all, delete-orphan", passive_deletes=True
    )