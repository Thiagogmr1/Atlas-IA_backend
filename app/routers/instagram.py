from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.repositories.instagram_repository import InstagramRepository
from app.routers.deps import get_current_user
from app.schemas.instagram import (
    InstagramAccountRead,
    InstagramConnectResponse,
    InstagramPublicationRead,
    InstagramPublishRequest,
)
from app.services.instagram_service import InstagramService

router = APIRouter(prefix="/api/integrations/instagram", tags=["Instagram Integration"])


def get_instagram_service(db: Session = Depends(get_db)) -> InstagramService:
    return InstagramService(InstagramRepository(db))


@router.post(
    "/connect",
    response_model=InstagramConnectResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar conexão OAuth do Instagram",
)
def connect_instagram(
    current_user: User = Depends(get_current_user),
    service: InstagramService = Depends(get_instagram_service),
):
    """Gera a URL oficial de autorização da Meta com token state seguro contra CSRF."""
    return service.generate_connect_url(current_user.id)


@router.get(
    "/callback",
    response_model=InstagramAccountRead,
    status_code=status.HTTP_200_OK,
    summary="Callback do fluxo OAuth do Instagram",
)
def oauth_callback(
    code: str = Query(..., description="Authorization code retornado pela Meta"),
    state: str = Query(..., description="Token state para proteção contra CSRF"),
    service: InstagramService = Depends(get_instagram_service),
):
    """Processa o retorno da Meta, valida o state, troca o code por token de longa duração,
    criptografa os dados e salva a conexão do Instagram.
    """
    return service.handle_oauth_callback(code=code, state=state)


@router.get(
    "",
    response_model=InstagramAccountRead,
    status_code=status.HTTP_200_OK,
    summary="Consultar status da conta do Instagram conectada",
)
def get_instagram_account(
    current_user: User = Depends(get_current_user),
    service: InstagramService = Depends(get_instagram_service),
):
    """Retorna os dados públicos da conta conectada (username, foto, status). NUNCA expõe tokens."""
    return service.get_account_status(current_user.id)


@router.delete(
    "",
    status_code=status.HTTP_200_OK,
    summary="Desconectar conta do Instagram",
)
def disconnect_instagram(
    current_user: User = Depends(get_current_user),
    service: InstagramService = Depends(get_instagram_service),
):
    """Desconecta a conta do Instagram e remove as credenciais com segurança."""
    return service.disconnect_account(current_user.id)


@router.post(
    "/publish",
    status_code=status.HTTP_200_OK,
    summary="Publicar conteúdo no Instagram",
)
def publish_to_instagram(
    data: InstagramPublishRequest,
    current_user: User = Depends(get_current_user),
    service: InstagramService = Depends(get_instagram_service),
):
    """Publica fotos, vídeos, Reels ou carrosséis no Instagram via Graph API oficial.
    Se user_approval_confirmed=False, retorna a prévia e aguarda aprovação explícita.
    """
    return service.publish_content(current_user.id, data)


@router.get(
    "/publications",
    response_model=List[InstagramPublicationRead],
    status_code=status.HTTP_200_OK,
    summary="Histórico de publicações do usuário",
)
def list_instagram_publications(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    service: InstagramService = Depends(get_instagram_service),
):
    """Lista as publicações realizadas no Instagram pelo usuário atual."""
    return service.list_user_publications(current_user.id, limit=limit, offset=offset)


@router.get(
    "/publications/{id}",
    response_model=InstagramPublicationRead,
    status_code=status.HTTP_200_OK,
    summary="Detalhes de uma publicação",
)
def get_instagram_publication(
    id: int,
    current_user: User = Depends(get_current_user),
    service: InstagramService = Depends(get_instagram_service),
):
    """Recupera os detalhes de uma publicação específica com validação de isolamento por usuário."""
    return service.get_user_publication(id, current_user.id)
