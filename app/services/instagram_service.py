from datetime import datetime, timedelta, timezone
import json
import logging
from typing import Any, Dict, List, Optional
import httpx
import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.instagram import InstagramIntegration, InstagramPostPayload
from app.models.instagram import InstagramIntegration as InstagramIntegrationModel, InstagramPublication
from app.repositories.instagram_repository import InstagramRepository
from app.schemas.instagram import (
    InstagramAccountRead,
    InstagramConnectResponse,
    InstagramPublicationRead,
    InstagramPublishRequest,
)
from app.security.encryption import decrypt_token, encrypt_token

logger = logging.getLogger(__name__)

INSTAGRAM_SCOPES = "instagram_business_basic,instagram_business_content_publish"


class InstagramService:
    """Serviço de gerenciamento da integração e publicações no Instagram."""

    def __init__(
        self,
        repository: InstagramRepository,
        http_client: Optional[httpx.Client] = None,
        integration_client: Optional[InstagramIntegration] = None,
    ):
        self.repo = repository
        self.http_client = http_client or httpx.Client(timeout=30.0)
        self.instagram_client = integration_client or InstagramIntegration(http_client=self.http_client)

    def generate_connect_url(self, user_id: int) -> InstagramConnectResponse:
        """Gera URL de autorização OAuth com token state assinado contra CSRF."""
        if not settings.meta_app_id:
            logger.warning("META_APP_ID não configurado no .env")

        # Gera token state seguro assinado com JWT e validade de 15 minutos
        state_payload = {
            "user_id": user_id,
            "purpose": "instagram_oauth",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        }
        state_token = jwt.encode(state_payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

        # URL oficial do fluxo Instagram Login / Meta OAuth
        base_auth_url = f"https://www.facebook.com/{settings.meta_api_version}/dialog/oauth"
        params = {
            "client_id": settings.meta_app_id,
            "redirect_uri": settings.instagram_redirect_uri,
            "scope": INSTAGRAM_SCOPES,
            "response_type": "code",
            "state": state_token,
        }
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        auth_url = f"{base_auth_url}?{query_string}"

        return InstagramConnectResponse(auth_url=auth_url, state=state_token)

    def handle_oauth_callback(self, code: str, state: str) -> InstagramAccountRead:
        """Valida o state contra CSRF, troca code por token de longa duração e salva a conexão."""
        # 1. Validação estrita de CSRF via state
        try:
            payload = jwt.decode(
                state, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
            )
            if payload.get("purpose") != "instagram_oauth":
                raise ValueError("State com propósito inválido")
            user_id = int(payload["user_id"])
        except Exception as exc:
            logger.error("Falha na validação do state OAuth: %s", exc.__class__.__name__)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="State de autorização inválido ou expirado. Tente conectar novamente.",
            )

        # 2. Troca do authorization code por token de acesso de curta duração
        token_endpoint = f"https://graph.facebook.com/{settings.meta_api_version}/oauth/access_token"
        try:
            token_resp = self.http_client.get(
                token_endpoint,
                params={
                    "client_id": settings.meta_app_id,
                    "client_secret": settings.meta_app_secret,
                    "redirect_uri": settings.instagram_redirect_uri,
                    "code": code,
                },
            )
            token_data = token_resp.json()
            if token_resp.status_code != 200 or "access_token" not in token_data:
                err_msg = token_data.get("error", {}).get("message", "Falha ao obter token OAuth da Meta")
                logger.error("Erro OAuth Meta: %s", err_msg)
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Falha na autorização com a Meta.")

            short_token = token_data["access_token"]
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Exceção na chamada de token OAuth: %s", exc)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Erro de conexão com os servidores da Meta.")

        # 3. Troca do token de curta duração por Long-Lived Token (60 dias)
        long_lived_token = short_token
        expires_at = datetime.now(timezone.utc) + timedelta(days=60)
        try:
            exchange_resp = self.http_client.get(
                token_endpoint,
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": settings.meta_app_id,
                    "client_secret": settings.meta_app_secret,
                    "fb_exchange_token": short_token,
                },
            )
            if exchange_resp.status_code == 200:
                exchange_data = exchange_resp.json()
                long_lived_token = exchange_data.get("access_token", short_token)
                expires_in_sec = exchange_data.get("expires_in", 60 * 86400)
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_sec)
        except Exception:
            logger.warning("Não foi possível trocar por long-lived token, utilizando token inicial.")

        # 4. Busca dados da conta profissional do Instagram
        try:
            user_info_resp = self.http_client.get(
                f"https://graph.facebook.com/{settings.meta_api_version}/me/accounts",
                params={"access_token": long_lived_token, "fields": "instagram_business_account{id,username,profile_picture_url}"},
            )
            ig_id = "unknown"
            username = "instagram_business"
            profile_pic = None

            if user_info_resp.status_code == 200:
                accounts_data = user_info_resp.json().get("data", [])
                for acc in accounts_data:
                    if "instagram_business_account" in acc:
                        ig_account = acc["instagram_business_account"]
                        ig_id = ig_account.get("id", ig_id)
                        username = ig_account.get("username", username)
                        profile_pic = ig_account.get("profile_picture_url")
                        break
        except Exception as exc:
            logger.warning("Falha ao recuperar dados adicionais da conta: %s", exc)

        # 5. Criptografia AES-256-GCM do token antes do armazenamento
        encrypted_token = encrypt_token(long_lived_token)

        # 6. Gravação segura no banco
        integration = self.repo.save_integration(
            user_id=user_id,
            instagram_user_id=ig_id,
            username=username,
            access_token_encrypted=encrypted_token,
            profile_picture_url=profile_pic,
            token_expires_at=expires_at,
            scopes=INSTAGRAM_SCOPES,
        )

        return InstagramAccountRead(
            connected=True,
            instagram_user_id=integration.instagram_user_id,
            username=integration.username,
            profile_picture_url=integration.profile_picture_url,
            connection_status=integration.connection_status,
            token_expires_at=integration.token_expires_at,
            scopes=integration.scopes,
            created_at=integration.created_at,
        )

    def get_account_status(self, user_id: int) -> InstagramAccountRead:
        """Retorna o status e os dados públicos da conta conectada (sem tokens)."""
        integration = self.repo.get_integration_by_user(user_id)
        if not integration:
            return InstagramAccountRead(connected=False, connection_status="disconnected")

        return InstagramAccountRead(
            connected=True,
            instagram_user_id=integration.instagram_user_id,
            username=integration.username,
            profile_picture_url=integration.profile_picture_url,
            connection_status=integration.connection_status,
            token_expires_at=integration.token_expires_at,
            scopes=integration.scopes,
            created_at=integration.created_at,
        )

    def disconnect_account(self, user_id: int) -> Dict[str, Any]:
        """Desconecta a conta do Instagram do usuário."""
        deleted = self.repo.delete_integration(user_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhuma conta do Instagram conectada para desconectar.",
            )
        return {"success": True, "message": "Conta do Instagram desconectada com sucesso."}

    def publish_content(
        self, user_id: int, request: InstagramPublishRequest
    ) -> Dict[str, Any]:
        """Executa a publicação real ou gera a prévia para aprovação obrigatória."""
        # 1. Recupera a integração ativa
        integration = self.repo.get_integration_by_user(user_id)
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhuma conta do Instagram conectada. Conecte sua conta antes de publicar.",
            )

        # 2. Prevenção de duplicidade
        media_ref = json.dumps(request.media_urls)
        duplicate = self.repo.check_recent_duplicate(user_id, request.caption, media_ref)
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Publicação idêntica já realizada nos últimos 10 minutos para evitar duplicidade.",
            )

        payload = InstagramPostPayload(
            caption=request.caption,
            media_type=request.media_type,
            media_urls=request.media_urls,
            hashtags=request.hashtags,
        )

        validation = self.instagram_client.validate_post(payload)
        if not validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "Falha na validação técnica do post", "issues": validation["issues"]},
            )

        # 3. Modo com aprovação: se ainda não aprovado, grava como rascunho/pendente
        if not request.user_approval_confirmed:
            pub_record = self.repo.create_publication(
                user_id=user_id,
                integration_id=integration.id,
                media_type=request.media_type,
                caption=validation["final_caption"],
                media_reference=media_ref,
                publication_status="pending_approval",
            )
            return {
                "success": True,
                "status": "awaiting_user_approval",
                "publication_id": pub_record.id,
                "preview": validation,
                "message": "Prévia gerada com sucesso. Confirme a aprovação para publicar no Instagram.",
            }

        # 4. Registra no banco como em processamento
        pub_record = self.repo.create_publication(
            user_id=user_id,
            integration_id=integration.id,
            media_type=request.media_type,
            caption=validation["final_caption"],
            media_reference=media_ref,
            publication_status="publishing",
        )

        # 5. Descriptografa token estritamente no backend
        try:
            token = decrypt_token(integration.access_token_encrypted)
        except Exception:
            self.repo.update_publication_status(
                pub_record.id,
                status="failed",
                error_message="Falha na descriptografia do token de acesso.",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao recuperar credenciais para publicação.",
            )

        # 6. Executa chamada real à Instagram Graph API
        result = self.instagram_client.publish_to_instagram(
            access_token=token,
            ig_user_id=integration.instagram_user_id,
            payload=payload,
        )

        if result.get("success"):
            media_id = result.get("published_media_id")
            self.repo.update_publication_status(
                pub_record.id,
                status="published",
                instagram_media_id=media_id,
                published_at=datetime.now(timezone.utc),
            )
            return {
                "success": True,
                "publication_id": pub_record.id,
                "instagram_media_id": media_id,
                "published_media_id": media_id,
                "instagram_post_url": result.get("instagram_post_url"),
                "status": "published",
                "published_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            err = result.get("error", "Erro desconhecido na publicação da API")
            self.repo.update_publication_status(
                pub_record.id,
                status="failed",
                error_message=str(err),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Falha na publicação pela Instagram API: {err}",
            )

    def list_user_publications(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> List[InstagramPublicationRead]:
        """Lista histórico de publicações do usuário autenticado."""
        pubs = self.repo.list_publications(user_id, limit, offset)
        return [InstagramPublicationRead.model_validate(p) for p in pubs]

    def get_user_publication(
        self, pub_id: int, user_id: int
    ) -> InstagramPublicationRead:
        """Recupera publicação individual com isolamento de usuário."""
        pub = self.repo.get_publication(pub_id, user_id)
        if not pub:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Publicação não encontrada.",
            )
        return InstagramPublicationRead.model_validate(pub)
