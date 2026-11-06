from typing import Any, List, Optional
from pydantic import BaseModel, Field

from app.agent.context import AgentContext
from app.integrations.instagram import InstagramIntegration, InstagramPostPayload
from app.models.enums import AdPlatform, AgentActionStatus, AgentActionType
from app.services.creative_studio_service import CreativeStudioService
from app.services.media_service import MediaService
from app.tools.base import AgentTool


# ==============================================================================
# 8. generate_advertising_image (Creative Studio)
# ==============================================================================
class GenerateAdvertisingImageArgs(BaseModel):
    prompt: str = Field(..., description="Descrição detalhada da arte publicitária a ser criada")
    product_category: str = Field(default="geral", description="Categoria: perfume, roupas, cosméticos, alimentos, eletrônicos, etc.")
    aesthetic_style: str = Field(default="premium", description="Estilo: premium, minimalista, vibrante, luxo, urbano, etc.")
    aspect_ratio: str = Field(default="1:1", description="Proporção: 1:1 (feed quadrado), 4:5 (feed retrato), 9:16 (stories/reels) ou 16:9 (horizontal)")
    color_palette: Optional[str] = Field(default=None, description="Cores da marca ou preferências visuais")
    reference_notes: Optional[str] = Field(default=None, description="Instruções ou referências de identidade visual")


class GenerateAdvertisingImageTool(AgentTool):
    name = "generate_advertising_image"
    description = (
        "Gera imagens e designs publicitários profissionais do zero para produtos (perfumes, roupas, "
        "cosméticos, eletrônicos, etc.) adaptados para Instagram Feed, Stories e outros canais."
    )
    args_schema = GenerateAdvertisingImageArgs

    def __init__(self, studio_service: CreativeStudioService | None = None):
        self.studio = studio_service or CreativeStudioService()

    def execute(self, context: AgentContext, **kwargs) -> dict[str, Any]:
        result = self.studio.generate_advertising_image(
            prompt=kwargs.get("prompt", ""),
            product_category=kwargs.get("product_category", "geral"),
            aesthetic_style=kwargs.get("aesthetic_style", "premium"),
            aspect_ratio=kwargs.get("aspect_ratio", "1:1"),
            color_palette=kwargs.get("color_palette"),
            reference_notes=kwargs.get("reference_notes"),
        )
        result["user_id"] = context.user_id
        return result


# ==============================================================================
# 9. adapt_creative_image (Creative Studio)
# ==============================================================================
class AdaptCreativeImageArgs(BaseModel):
    base_image_url: str = Field(..., description="URL da imagem anterior a ser ajustada")
    adjustments: str = Field(..., description="Modificações solicitadas (ex: trocar cor do fundo, adicionar elemento, mudar proporção)")
    new_aspect_ratio: Optional[str] = Field(default=None, description="Nova proporção se desejada: 1:1, 4:5, 9:16 ou 16:9")


class AdaptCreativeImageTool(AgentTool):
    name = "adapt_creative_image"
    description = (
        "Adapta uma peça visual já gerada, permitindo ajustes conversacionais como trocar fundo, "
        "cores, elementos e redimensionar para outros formatos (ex: Feed para Stories)."
    )
    args_schema = AdaptCreativeImageArgs

    def __init__(self, studio_service: CreativeStudioService | None = None):
        self.studio = studio_service or CreativeStudioService()

    def execute(self, context: AgentContext, **kwargs) -> dict[str, Any]:
        return self.studio.adapt_image(
            base_image_url=kwargs.get("base_image_url", ""),
            adjustments=kwargs.get("adjustments", ""),
            new_aspect_ratio=kwargs.get("new_aspect_ratio"),
        )


# ==============================================================================
# 10. analyze_uploaded_media
# ==============================================================================
class AnalyzeUploadedMediaArgs(BaseModel):
    media_url: str = Field(..., description="URL ou caminho da imagem ou vídeo enviado pelo usuário")
    analysis_goal: Optional[str] = Field(default=None, description="Foco da análise (ex: identificar produto, avaliar iluminação, criar legenda)")


class AnalyzeUploadedMediaTool(AgentTool):
    name = "analyze_uploaded_media"
    description = (
        "Analisa imagens e vídeos enviados pelo usuário via chat usando visão computacional da Gemini API. "
        "Identifica produtos, elementos visuais, qualidade estética e sugere melhorias e legendas."
    )
    args_schema = AnalyzeUploadedMediaArgs

    def __init__(self, media_service: MediaService | None = None):
        self.media_service = media_service or MediaService()

    def execute(self, context: AgentContext, **kwargs) -> dict[str, Any]:
        media_url = kwargs.get("media_url", "")
        # Resolve caminho em disco local a partir de /media/...
        if media_url.startswith("/media/"):
            rel_part = media_url.replace("/media/", "")
            file_path = self.media_service.base_upload_dir / rel_part
        else:
            file_path = media_url

        return self.media_service.analyze_media(
            file_path=file_path,
            analysis_goal=kwargs.get("analysis_goal"),
        )


# ==============================================================================
# 11. publish_instagram_post (Publicação Real com Aprovação)
# ==============================================================================
class PublishInstagramPostArgs(BaseModel):
    caption: str = Field(..., max_length=2200, description="Legenda completa da publicação")
    media_type: str = Field(..., description="IMAGE, VIDEO, REELS ou CAROUSEL")
    media_urls: List[str] = Field(..., min_length=1, description="Lista de URLs de imagem ou vídeo")
    hashtags: Optional[List[str]] = Field(default=None, description="Lista opcional de hashtags")
    user_approval_confirmed: bool = Field(
        ...,
        description="DEVE ser True se o usuário explicitamente confirmou a aprovação para publicar no Instagram. Caso ainda não tenha aprovado, DEVE ser False.",
    )
    scheduled_for: Optional[str] = Field(default=None, description="Data/hora agendada em formato ISO")


class PublishInstagramPostTool(AgentTool):
    name = "publish_instagram_post"
    description = (
        "Publica conteúdo (fotos, reels, vídeos ou carrosséis) na conta do Instagram conectada via Meta Graph API. "
        "EXIGE aprovação explícita do usuário antes da publicação real. Não simula."
    )
    args_schema = PublishInstagramPostArgs

    def __init__(self, instagram_integration: InstagramIntegration | None = None):
        self.integration = instagram_integration or InstagramIntegration()

    def execute(self, context: AgentContext, **kwargs) -> dict[str, Any]:
        payload = InstagramPostPayload(
            caption=kwargs.get("caption", ""),
            media_type=kwargs.get("media_type", "IMAGE"),
            media_urls=kwargs.get("media_urls", []),
            hashtags=kwargs.get("hashtags"),
            scheduled_for=None,
        )

        validation = self.integration.validate_post(payload)

        # 1. Se o usuário ainda não confirmou, exibe a prévia e solicita aprovação
        if not kwargs.get("user_approval_confirmed", False):
            return {
                "success": True,
                "status": "awaiting_user_approval",
                "message": (
                    "Aqui está a prévia da sua publicação no Instagram. "
                    "Por favor, confirme se aprova a publicação respondendo 'Aprovo a publicação'."
                ),
                "preview": validation,
            }

        # 2. Se o usuário confirmou, busca integração ativa via InstagramService ou AdAccount
        db = getattr(context, "db_session", None)
        if not db:
            return {
                "success": False,
                "error": "Sessão de banco de dados indisponível no contexto do agente.",
            }

        from app.repositories.instagram_repository import InstagramRepository
        from app.services.instagram_service import InstagramService
        from app.schemas.instagram import InstagramPublishRequest

        repo = InstagramRepository(db)
        service = InstagramService(repo, integration_client=self.integration)

        try:
            req = InstagramPublishRequest(
                caption=kwargs.get("caption", ""),
                media_type=kwargs.get("media_type", "IMAGE"),
                media_urls=kwargs.get("media_urls", []),
                hashtags=kwargs.get("hashtags"),
                user_approval_confirmed=True,
            )
            pub_result = service.publish_content(context.user_id, req)
            return pub_result
        except Exception as exc:
            err_msg = str(getattr(exc, "detail", str(exc)))
            return {
                "success": False,
                "error": f"Não foi possível publicar no Instagram: {err_msg}",
                "status": "missing_account" if "Nenhuma conta" in err_msg else "failed",
            }

