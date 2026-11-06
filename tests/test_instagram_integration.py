from datetime import datetime, timedelta, timezone
import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.agent.context import AgentContext
from app.core.config import settings
from app.main import app
from app.models.instagram import InstagramIntegration, InstagramPublication
from app.models.user import User
from app.repositories.instagram_repository import InstagramRepository
from app.routers.deps import get_current_user
from app.routers.instagram import get_instagram_service
from app.schemas.instagram import InstagramPublishRequest
from app.security.encryption import decrypt_token, encrypt_token, TokenEncryptionError
from app.services.instagram_service import InstagramService
from app.tools.instagram_agent_tools import (
    GenerateInstagramPostTool,
    GetInstagramAccountTool,
    GetInstagramConnectionTool,
    GetInstagramPublicationsTool,
)
from app.tools.creative_studio_tools import PublishInstagramPostTool


# ==============================================================================
# 1. Testes de Criptografia AES-256-GCM
# ==============================================================================
def test_token_encryption_and_decryption_success():
    plain_token = "EAAB1234567890abcdef_SecretInstagramAccessToken_XYZ"
    encrypted = encrypt_token(plain_token)

    assert encrypted != plain_token
    assert len(encrypted) > len(plain_token)

    decrypted = decrypt_token(encrypted)
    assert decrypted == plain_token


def test_token_decryption_tampered_fails():
    plain_token = "EAAB123_test_token"
    encrypted = encrypt_token(plain_token)

    # Altera payload criptografado
    tampered = encrypted[:-4] + "AAAA"
    with pytest.raises(TokenEncryptionError):
        decrypt_token(tampered)


def test_token_encryption_empty_fails():
    with pytest.raises(TokenEncryptionError):
        encrypt_token("")


# ==============================================================================
# 2. Testes de OAuth e Validação de State (CSRF)
# ==============================================================================
def test_oauth_generate_connect_url():
    mock_repo = MagicMock()
    service = InstagramService(mock_repo)

    response = service.generate_connect_url(user_id=42)
    assert "https://www.facebook.com" in response.auth_url
    assert "instagram_business_basic" in response.auth_url
    assert response.state is not None


def test_oauth_callback_invalid_state_csrf_blocked():
    mock_repo = MagicMock()
    service = InstagramService(mock_repo)

    with pytest.raises(HTTPException) as exc_info:
        service.handle_oauth_callback(code="valid_code", state="forged_invalid_state")

    assert exc_info.value.status_code == 400
    assert "State de autorização inválido" in exc_info.value.detail


def test_oauth_callback_full_flow_success():
    mock_repo = MagicMock()
    mock_http = MagicMock()

    # Simula resposta do token de curta duração
    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {"access_token": "short_lived_token_123"}

    # Simula resposta do token de longa duração
    mock_exchange_resp = MagicMock()
    mock_exchange_resp.status_code = 200
    mock_exchange_resp.json.return_value = {
        "access_token": "long_lived_token_456",
        "expires_in": 5184000,  # 60 dias
    }

    # Simula resposta dos dados da conta
    mock_me_resp = MagicMock()
    mock_me_resp.status_code = 200
    mock_me_resp.json.return_value = {
        "data": [
            {
                "instagram_business_account": {
                    "id": "17841400000000001",
                    "username": "minhaloja_oficial",
                    "profile_picture_url": "https://cdn.instagram.com/pic.jpg",
                }
            }
        ]
    }

    mock_http.get.side_effect = [mock_token_resp, mock_exchange_resp, mock_me_resp]

    # Simula retorno do repositório
    now = datetime.now(timezone.utc)
    mock_integration = InstagramIntegration(
        id=1,
        user_id=10,
        instagram_user_id="17841400000000001",
        username="minhaloja_oficial",
        access_token_encrypted=encrypt_token("long_lived_token_456"),
        profile_picture_url="https://cdn.instagram.com/pic.jpg",
        token_expires_at=now + timedelta(days=60),
        scopes="instagram_business_basic,instagram_business_content_publish",
        connection_status="connected",
        created_at=now,
    )
    mock_repo.save_integration.return_value = mock_integration

    service = InstagramService(mock_repo, http_client=mock_http)
    connect_info = service.generate_connect_url(user_id=10)

    # Executa o callback com o state válido gerado
    account_read = service.handle_oauth_callback(code="auth_code_xyz", state=connect_info.state)

    assert account_read.connected is True
    assert account_read.username == "minhaloja_oficial"
    assert account_read.instagram_user_id == "17841400000000001"
    # Garante que nenhum token seja exposto no objeto lido
    assert not hasattr(account_read, "access_token")
    assert not hasattr(account_read, "access_token_encrypted")


# ==============================================================================
# 3. Testes de Isolamento Multiusuário e Consulta
# ==============================================================================
def test_get_account_status_isolated_and_safe():
    mock_repo = MagicMock()
    now = datetime.now(timezone.utc)
    mock_repo.get_integration_by_user.return_value = InstagramIntegration(
        id=1,
        user_id=15,
        instagram_user_id="1784149999",
        username="marca_15",
        profile_picture_url=None,
        access_token_encrypted=encrypt_token("token_secret"),
        token_expires_at=now + timedelta(days=30),
        scopes="scopes",
        connection_status="connected",
        created_at=now,
    )

    service = InstagramService(mock_repo)
    result = service.get_account_status(user_id=15)

    assert result.connected is True
    assert result.username == "marca_15"
    assert "token_secret" not in str(result.model_dump())
    assert "access_token" not in result.model_dump()


def test_disconnect_account_isolated():
    mock_repo = MagicMock()
    mock_repo.delete_integration.return_value = True

    service = InstagramService(mock_repo)
    res = service.disconnect_account(user_id=20)

    mock_repo.delete_integration.assert_called_once_with(20)
    assert res["success"] is True


# ==============================================================================
# 4. Testes de Publicação: Imagem, Reels, Carrossel e Prevenção de Duplicatas
# ==============================================================================
def test_publish_content_requires_user_approval():
    mock_repo = MagicMock()
    mock_repo.get_integration_by_user.return_value = InstagramIntegration(
        id=1, user_id=1, instagram_user_id="123", access_token_encrypted="enc"
    )
    mock_repo.check_recent_duplicate.return_value = None

    now = datetime.now(timezone.utc)
    mock_pub = InstagramPublication(
        id=101,
        user_id=1,
        integration_id=1,
        media_type="IMAGE",
        caption="Texto",
        media_reference="ref",
        publication_status="pending_approval",
        created_at=now,
    )
    mock_repo.create_publication.return_value = mock_pub

    service = InstagramService(mock_repo)
    req = InstagramPublishRequest(
        caption="Post para conferir prévia",
        media_type="IMAGE",
        media_urls=["https://exemplo.com/foto.jpg"],
        user_approval_confirmed=False,
    )

    result = service.publish_content(user_id=1, request=req)
    assert result["status"] == "awaiting_user_approval"
    assert result["publication_id"] == 101
    mock_repo.create_publication.assert_called_once()


def test_publish_content_duplicate_prevention_raises_conflict():
    mock_repo = MagicMock()
    mock_repo.get_integration_by_user.return_value = InstagramIntegration(id=1, user_id=1)
    # Simula publicação duplicada recente
    mock_repo.check_recent_duplicate.return_value = InstagramPublication(id=99)

    service = InstagramService(mock_repo)
    req = InstagramPublishRequest(
        caption="Legenda idêntica",
        media_type="IMAGE",
        media_urls=["https://exemplo.com/foto.jpg"],
        user_approval_confirmed=True,
    )

    with pytest.raises(HTTPException) as exc_info:
        service.publish_content(user_id=1, request=req)

    assert exc_info.value.status_code == 409
    assert "evitar duplicidade" in exc_info.value.detail


def test_publish_carousel_success():
    mock_repo = MagicMock()
    real_token = "EAAB_test_token_valid"
    enc_token = encrypt_token(real_token)
    mock_repo.get_integration_by_user.return_value = InstagramIntegration(
        id=5,
        user_id=2,
        instagram_user_id="17841400000000002",
        access_token_encrypted=enc_token,
    )
    mock_repo.check_recent_duplicate.return_value = None

    now = datetime.now(timezone.utc)
    mock_pub = InstagramPublication(
        id=202,
        user_id=2,
        integration_id=5,
        media_type="CAROUSEL",
        caption="Carrossel",
        media_reference="ref",
        publication_status="publishing",
        created_at=now,
    )
    mock_repo.create_publication.return_value = mock_pub

    # Simula chamadas HTTP para os itens e container do carrossel
    mock_http = MagicMock()
    item1_resp = MagicMock(status_code=200, json=lambda: {"id": "item_1"})
    item2_resp = MagicMock(status_code=200, json=lambda: {"id": "item_2"})
    carousel_container = MagicMock(status_code=200, json=lambda: {"id": "carousel_container_id"})
    publish_resp = MagicMock(status_code=200, json=lambda: {"id": "17841499999999999"})

    mock_http.post.side_effect = [item1_resp, item2_resp, carousel_container, publish_resp]

    service = InstagramService(mock_repo, http_client=mock_http)
    req = InstagramPublishRequest(
        caption="Carrossel com 2 fotos de alta qualidade",
        media_type="CAROUSEL",
        media_urls=["https://exemplo.com/foto1.jpg", "https://exemplo.com/foto2.jpg"],
        user_approval_confirmed=True,
    )

    result = service.publish_content(user_id=2, request=req)

    assert result["success"] is True
    assert result["instagram_media_id"] == "17841499999999999"
    assert "instagram.com/p/17841499999999999/" in result["instagram_post_url"]
    assert mock_http.post.call_count == 4


# ==============================================================================
# 5. Testes de Ferramentas do Agente (Section 4)
# ==============================================================================
def test_agent_tool_get_instagram_account():
    tool = GetInstagramAccountTool()
    mock_db = MagicMock()
    now = datetime.now(timezone.utc)
    mock_db.scalar.return_value = InstagramIntegration(
        id=1,
        user_id=7,
        instagram_user_id="17841400000000007",
        username="loja_da_roberta",
        profile_picture_url="https://pic.jpg",
        access_token_encrypted=encrypt_token("tok"),
        connection_status="connected",
        created_at=now,
    )

    ctx = AgentContext(user_id=7, user_name="Roberta", conversation_id=1, db_session=mock_db)
    res = tool.validate_and_execute(ctx, {})

    assert res["success"] is True
    assert res["connected"] is True
    assert res["username"] == "loja_da_roberta"
    # Garante que nenhum segredo esteja no retorno para o LLM
    assert "tok" not in str(res)


def test_agent_tool_get_instagram_connection():
    tool = GetInstagramConnectionTool()
    mock_db = MagicMock()
    mock_db.scalar.return_value = None  # Desconectado

    ctx = AgentContext(user_id=8, user_name="Lucas", conversation_id=2, db_session=mock_db)
    res = tool.validate_and_execute(ctx, {})

    assert res["success"] is True
    assert res["is_connected"] is False


def test_agent_tool_generate_instagram_post():
    tool = GenerateInstagramPostTool()
    ctx = AgentContext(user_id=1, user_name="User", conversation_id=1)
    res = tool.validate_and_execute(ctx, {"topic": "perfume importado", "post_format": "feed_imagem"})

    assert res["success"] is True
    pkg = res["post_package"]
    assert "perfume importado" in pkg["hook"]
    assert len(pkg["hashtags"]) >= 3
    assert pkg["is_within_limit"] is True


def test_agent_tool_get_instagram_publications():
    tool = GetInstagramPublicationsTool()
    mock_db = MagicMock()
    now = datetime.now(timezone.utc)
    mock_pub = InstagramPublication(
        id=10,
        user_id=1,
        integration_id=1,
        media_type="IMAGE",
        caption="Legenda de teste",
        media_reference="ref",
        publication_status="published",
        instagram_media_id="17841411111",
        published_at=now,
        created_at=now,
    )
    mock_db.scalars.return_value = [mock_pub]

    ctx = AgentContext(user_id=1, user_name="User", conversation_id=1, db_session=mock_db)
    res = tool.validate_and_execute(ctx, {"limit": 5})

    assert res["success"] is True
    assert res["total"] == 1
    assert res["publications"][0]["instagram_media_id"] == "17841411111"


# ==============================================================================
# 6. Testes dos Endpoints HTTP
# ==============================================================================
def test_endpoint_connect_instagram():
    client = TestClient(app)
    user = User(id=1, name="Gabriel", email="gabriel@atlasai.com")

    app.dependency_overrides[get_current_user] = lambda: user

    try:
        response = client.post("/api/integrations/instagram/connect")
        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data
        assert "state" in data
        assert "instagram_business_content_publish" in data["auth_url"]
    finally:
        app.dependency_overrides.clear()


def test_endpoint_get_account_status_unconnected():
    client = TestClient(app)
    user = User(id=99, name="Novo Usuario", email="novo@test.com")
    mock_service = MagicMock()
    mock_service.get_account_status.return_value = {
        "connected": False,
        "connection_status": "disconnected",
        "username": None,
        "profile_picture_url": None,
        "token_expires_at": None,
        "scopes": None,
        "created_at": None,
        "instagram_user_id": None,
    }

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_instagram_service] = lambda: mock_service

    try:
        response = client.get("/api/integrations/instagram")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False
    finally:
        app.dependency_overrides.clear()
