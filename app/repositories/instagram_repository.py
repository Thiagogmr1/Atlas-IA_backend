from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.instagram import InstagramIntegration, InstagramPublication


class InstagramRepository:
    """Repositório para persistência de integrações e publicações do Instagram."""

    def __init__(self, db: Session):
        self.db = db

    def get_integration_by_user(self, user_id: int) -> Optional[InstagramIntegration]:
        """Recupera a integração ativa do Instagram para o usuário especificado."""
        stmt = select(InstagramIntegration).where(
            InstagramIntegration.user_id == user_id,
            InstagramIntegration.connection_status == "connected",
        )
        return self.db.scalar(stmt)

    def save_integration(
        self,
        user_id: int,
        instagram_user_id: str,
        username: str,
        access_token_encrypted: str,
        profile_picture_url: Optional[str] = None,
        token_expires_at: Optional[datetime] = None,
        scopes: Optional[str] = None,
    ) -> InstagramIntegration:
        """Cria ou atualiza a conexão do Instagram do usuário."""
        stmt = select(InstagramIntegration).where(InstagramIntegration.user_id == user_id)
        integration = self.db.scalar(stmt)

        if integration is None:
            integration = InstagramIntegration(
                user_id=user_id,
                instagram_user_id=instagram_user_id,
                username=username,
                access_token_encrypted=access_token_encrypted,
                profile_picture_url=profile_picture_url,
                token_expires_at=token_expires_at,
                scopes=scopes,
                connection_status="connected",
            )
            self.db.add(integration)
        else:
            integration.instagram_user_id = instagram_user_id
            integration.username = username
            integration.access_token_encrypted = access_token_encrypted
            integration.profile_picture_url = profile_picture_url
            integration.token_expires_at = token_expires_at
            integration.scopes = scopes
            integration.connection_status = "connected"
            integration.updated_at = func.now()

        self.db.commit()
        self.db.refresh(integration)
        return integration

    def delete_integration(self, user_id: int) -> bool:
        """Remove a integração do Instagram do usuário (desconexão segura)."""
        stmt = select(InstagramIntegration).where(InstagramIntegration.user_id == user_id)
        integration = self.db.scalar(stmt)
        if integration:
            self.db.delete(integration)
            self.db.commit()
            return True
        return False

    def create_publication(
        self,
        user_id: int,
        integration_id: int,
        media_type: str,
        caption: str,
        media_reference: str,
        publication_status: str = "draft",
    ) -> InstagramPublication:
        """Registra uma publicação no banco de dados."""
        pub = InstagramPublication(
            user_id=user_id,
            integration_id=integration_id,
            media_type=media_type,
            caption=caption,
            media_reference=media_reference,
            publication_status=publication_status,
        )
        self.db.add(pub)
        self.db.commit()
        self.db.refresh(pub)
        return pub

    def update_publication_status(
        self,
        publication_id: int,
        status: str,
        instagram_media_id: Optional[str] = None,
        error_message: Optional[str] = None,
        published_at: Optional[datetime] = None,
    ) -> Optional[InstagramPublication]:
        """Atualiza o status e os dados de confirmação da publicação."""
        stmt = select(InstagramPublication).where(InstagramPublication.id == publication_id)
        pub = self.db.scalar(stmt)
        if pub:
            pub.publication_status = status
            if instagram_media_id:
                pub.instagram_media_id = instagram_media_id
            if error_message:
                pub.error_message = error_message
            if published_at:
                pub.published_at = published_at
            self.db.commit()
            self.db.refresh(pub)
        return pub

    def list_publications(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> list[InstagramPublication]:
        """Lista as publicações pertencentes estritamente ao usuário informado."""
        stmt = (
            select(InstagramPublication)
            .where(InstagramPublication.user_id == user_id)
            .order_by(InstagramPublication.created_at.desc(), InstagramPublication.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(stmt))

    def get_publication(self, pub_id: int, user_id: int) -> Optional[InstagramPublication]:
        """Recupera uma publicação garantindo isolamento por usuário."""
        stmt = select(InstagramPublication).where(
            InstagramPublication.id == pub_id,
            InstagramPublication.user_id == user_id,
        )
        return self.db.scalar(stmt)

    def check_recent_duplicate(
        self, user_id: int, caption: str, media_reference: str, minutes: int = 10
    ) -> Optional[InstagramPublication]:
        """Verifica se existe publicação idêntica recente para prevenir duplicidade."""
        recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        stmt = select(InstagramPublication).where(
            InstagramPublication.user_id == user_id,
            InstagramPublication.caption == caption,
            InstagramPublication.media_reference == media_reference,
            InstagramPublication.created_at >= recent_cutoff,
            InstagramPublication.publication_status.in_(["published", "publishing"]),
        )
        return self.db.scalar(stmt)
