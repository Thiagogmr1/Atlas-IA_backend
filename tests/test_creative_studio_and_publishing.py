from unittest.mock import MagicMock
import pytest
from app.agent.context import AgentContext
from app.integrations.instagram import InstagramIntegration, InstagramPostPayload
from app.models.ad_account import AdAccount
from app.models.enums import AdAccountStatus, AdPlatform
from app.services.creative_studio_service import CreativeStudioService
from app.services.media_service import MediaService
from app.tools.creative_studio_tools import (
    AdaptCreativeImageTool,
    AnalyzeUploadedMediaTool,
    GenerateAdvertisingImageTool,
    PublishInstagramPostTool,
)

test_context = AgentContext(
    user_id=1,
    user_name="Gabriel",
    conversation_id=10,
)


def test_creative_studio_generate_advertising_image():
    service = CreativeStudioService()
    result = service.generate_advertising_image(
        prompt="Frasco de perfume com estética premium, fundo preto e detalhes dourados",
        product_category="perfume",
        aesthetic_style="luxo premium",
        aspect_ratio="1:1",
        color_palette="preto e dourado",
    )

    assert result["success"] is True
    assert result["aspect_ratio"] == "1:1"
    assert "Feed Quadrado" in result["format_description"]
    assert result["creative_url"].startswith("/media/generated/")


def test_creative_studio_adapt_image():
    service = CreativeStudioService()
    result = service.adapt_image(
        base_image_url="/media/generated/design_123.jpg",
        adjustments="Trocar fundo para mármore branco e mudar para formato stories",
        new_aspect_ratio="9:16",
    )

    assert result["success"] is True
    assert result["aspect_ratio"] == "9:16"
    assert "Stories" in result["format_description"]


def test_media_service_save_upload_valid_image():
    import io
    from PIL import Image

    service = MediaService()
    buf = io.BytesIO()
    img = Image.new("RGB", (20, 20), color="blue")
    img.save(buf, format="JPEG")
    valid_jpeg = buf.getvalue()

    saved = service.save_upload(
        file_bytes=valid_jpeg,
        original_filename="produto.jpg",
        content_type="image/jpeg",
        user_id=42,
    )

    assert saved["success"] is True
    assert "/media/users/42/" in saved["media_url"]
    assert saved["media_kind"] == "image"


def test_media_service_rejects_unsupported_mime():
    service = MediaService()
    with pytest.raises(ValueError) as exc:
        service.save_upload(
            file_bytes=b"executable binary",
            original_filename="virus.exe",
            content_type="application/x-msdownload",
            user_id=42,
        )
    assert "Formato de arquivo não suportado" in str(exc.value)


def test_publish_instagram_post_requires_explicit_user_approval():
    tool = PublishInstagramPostTool()

    # Quando user_approval_confirmed for False, deve apenas exibir a prévia e solicitar confirmação
    result = tool.validate_and_execute(
        test_context,
        {
            "caption": "Novo lançamento de perfume exclusivo!",
            "media_type": "IMAGE",
            "media_urls": ["https://cdn.exemplo.com/perfume.jpg"],
            "user_approval_confirmed": False,
        },
    )

    assert result["success"] is True
    assert result["status"] == "awaiting_user_approval"
    assert "confirme se aprova a publicação" in result["message"]
    assert result["preview"]["valid"] is True


def test_publish_instagram_post_fails_without_connected_account():
    tool = PublishInstagramPostTool()
    mock_db = MagicMock()
    mock_db.scalar.return_value = None  # Nenhuma conta conectada

    ctx_with_db = AgentContext(
        user_id=1,
        user_name="Gabriel",
        conversation_id=10,
        db_session=mock_db,
    )

    result = tool.validate_and_execute(
        ctx_with_db,
        {
            "caption": "Post aprovado para publicar",
            "media_type": "IMAGE",
            "media_urls": ["https://cdn.exemplo.com/post.jpg"],
            "user_approval_confirmed": True,
        },
    )

    assert result["success"] is False
    assert result["status"] == "missing_account"
    assert "Nenhuma conta do Instagram" in result["error"]


def test_publish_instagram_post_real_api_call_success():
    mock_http = MagicMock()

    # Simula retorno do contêiner da Meta
    mock_container_resp = MagicMock()
    mock_container_resp.status_code = 200
    mock_container_resp.json.return_value = {"id": "container_999888"}

    # Simula retorno da publicação da Meta
    mock_publish_resp = MagicMock()
    mock_publish_resp.status_code = 200
    mock_publish_resp.json.return_value = {"id": "17841400000000001"}

    mock_http.post.side_effect = [mock_container_resp, mock_publish_resp]

    integration = InstagramIntegration(http_client=mock_http)
    tool = PublishInstagramPostTool(instagram_integration=integration)

    from app.models.instagram import InstagramIntegration as InstagramIntegrationModel
    from app.security.encryption import encrypt_token

    # Simula integração do Instagram conectada
    ig_integration = InstagramIntegrationModel(
        id=1,
        user_id=1,
        instagram_user_id="17841405393048511",
        username="perfil_teste",
        access_token_encrypted=encrypt_token("EAAB...real_mock_token"),
        connection_status="connected",
    )
    mock_db = MagicMock()
    mock_db.scalar.side_effect = lambda stmt: ig_integration if "instagram_integrations" in str(stmt) else None

    ctx = AgentContext(user_id=1, user_name="Gabriel", conversation_id=10, db_session=mock_db)

    result = tool.validate_and_execute(
        ctx,
        {
            "caption": "Perfume sofisticado com acabamento dourado #luxo",
            "media_type": "IMAGE",
            "media_urls": ["https://exemplo.com/perfume.jpg"],
            "user_approval_confirmed": True,
        },
    )

    assert result["success"] is True
    assert result["published_media_id"] == "17841400000000001"
    assert "instagram.com/p/17841400000000001/" in result["instagram_post_url"]
    assert mock_http.post.call_count == 2
