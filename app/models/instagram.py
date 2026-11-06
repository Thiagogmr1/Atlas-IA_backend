from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InstagramIntegration(Base):
    __tablename__ = "instagram_integrations"
    __table_args__ = (UniqueConstraint("user_id", "instagram_user_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user.id", ondelete="CASCADE"), index=True
    )
    instagram_user_id: Mapped[str] = mapped_column(String(100), index=True)
    username: Mapped[str] = mapped_column(String(150))
    profile_picture_url: Mapped[Optional[str]] = mapped_column(Text)
    access_token_encrypted: Mapped[str] = mapped_column(Text)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    scopes: Mapped[Optional[str]] = mapped_column(Text)
    connection_status: Mapped[str] = mapped_column(String(50), default="connected")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    publications: Mapped[list["InstagramPublication"]] = relationship(
        back_populates="integration", cascade="all, delete-orphan", passive_deletes=True
    )


class InstagramPublication(Base):
    __tablename__ = "instagram_publications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user.id", ondelete="CASCADE"), index=True
    )
    integration_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("instagram_integrations.id", ondelete="CASCADE"), index=True
    )
    instagram_media_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    media_type: Mapped[str] = mapped_column(String(50))
    caption: Mapped[str] = mapped_column(Text)
    media_reference: Mapped[str] = mapped_column(Text)
    publication_status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    integration: Mapped["InstagramIntegration"] = relationship(back_populates="publications")
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
