from typing import Any, List, Optional
from pydantic import BaseModel, Field

from app.agent.context import AgentContext
from app.integrations.instagram import InstagramIntegration, InstagramPostPayload
from app.repositories.instagram_repository import InstagramRepository
from app.schemas.instagram import InstagramPublishRequest
from app.services.instagram_service import InstagramService
from app.tools.base import AgentTool


# ==============================================================================
# 1. get_instagram_account
# ==============================================================================
class EmptyArgs(BaseModel):
    pass


class GetInstagramAccountTool(AgentTool):
    name = "get_instagram_account"
    description = (
        "Consulta as informações da conta do Instagram conectada do usuário autenticado "
        "(username, status de conexão, id e foto de perfil). NUNCA expõe tokens."
    )
    args_schema = EmptyArgs

    def execute(self, context: AgentContext, **kwargs) -> dict[str, Any]:
        db = getattr(context, "db_session", None)
        if not db:
            return {"success": False, "error": "Sessão de banco indisponível no contexto."}

        repo = InstagramRepository(db)
        service = InstagramService(repo)
        status_data = service.get_account_status(context.user_id)
        return {
            "success": True,
            "connected": status_data.connected,
            "username": status_data.username,
            "instagram_user_id": status_data.instagram_user_id,
            "connection_status": status_data.connection_status,
            "profile_picture_url": status_data.profile_picture_url,
        }


# ==============================================================================
# 2. get_instagram_connection
# ==============================================================================
class GetInstagramConnectionTool(AgentTool):
    name = "get_instagram_connection"
    description = "Verifica se o usuário possui uma conta ativa do Instagram conectada ao AtlasAI."
    args_schema = EmptyArgs

    def execute(self, context: AgentContext, **kwargs) -> dict[str, Any]:
        db = getattr(context, "db_session", None)
        if not db:
            return {"success": False, "error": "Sessão de banco indisponível."}

        repo = InstagramRepository(db)
        service = InstagramService(repo)
        status_data = service.get_account_status(context.user_id)
        return {
            "success": True,
            "is_connected": status_data.connected,
            "status": status_data.connection_status,
            "username": status_data.username,
        }


# ==============================================================================
# 3. generate_instagram_post
# ==============================================================================
class GenerateInstagramPostArgs(BaseModel):
    topic: str = Field(..., description="Tema ou assunto do post")
    post_format: str = Field(default="feed_imagem", description="Formato: feed_imagem, carrossel, reels ou stories")
    target_audience: Optional[str] = Field(default=None, description="Público-alvo")
    tone: Optional[str] = Field(default="persuasivo", description="Tom: educativo, vendedor, inspiracional, divertido")
    call_to_action: Optional[str] = Field(default=None, description="Chamada para ação")
    suggest_hashtags: bool = Field(default=True, description="Se deve incluir hashtags recomendadas")


class GenerateInstagramPostTool(AgentTool):
    name = "generate_instagram_post"
    description = (
        "Gera um pacote completo de publicação para Instagram contendo gancho inicial, "
        "legenda estruturada com quebras de linha, CTA e bloco estratégico de hashtags."
    )
    args_schema = GenerateInstagramPostArgs

    def execute(self, context: AgentContext, **kwargs) -> dict[str, Any]:
        topic = kwargs.get("topic")
        fmt = kwargs.get("post_format", "feed_imagem")
        tone = kwargs.get("tone", "persuasivo")
        cta = kwargs.get("call_to_action") or "Comente abaixo o que você achou e compartilhe com alguém que precisa ver isso!"

        hook = f"Você já se perguntou como dominar {topic} de verdade? 👇"
        body = (
            f"No mercado atual, quem não aplica uma estratégia clara em {topic} acaba ficando para trás.\n\n"
            f"Confira 3 pilares fundamentais:\n"
            f"1️⃣ Foco na necessidade real do público;\n"
            f"2️⃣ Comunicação direta e transparente;\n"
            f"3️⃣ Consistência no posicionamento diário."
        )

        clean_topic = topic.replace(" ", "").lower()
        hashtags = [f"#{clean_topic}", f"#{clean_topic}brasil", "#marketingdigital", "#sucesso", "#conteudoestrategico"]
        tags_str = " ".join(hashtags)

        full_caption = f"{hook}\n\n{body}\n\n💬 {cta}\n\n{tags_str}"

        return {
            "success": True,
            "post_package": {
                "post_format": fmt,
                "tone": tone,
                "hook": hook,
                "caption": full_caption,
                "hashtags": hashtags,
                "char_count": len(full_caption),
                "is_within_limit": len(full_caption) <= 2200,
            },
        }


# ==============================================================================
# 4. get_instagram_publications
# ==============================================================================
class GetInstagramPublicationsArgs(BaseModel):
    limit: Optional[int] = Field(default=10, ge=1, le=50, description="Quantidade de publicações a recuperar")


class GetInstagramPublicationsTool(AgentTool):
    name = "get_instagram_publications"
    description = "Consulta o histórico de publicações realizadas e o status de cada post no Instagram para o usuário atual."
    args_schema = GetInstagramPublicationsArgs

    def execute(self, context: AgentContext, **kwargs) -> dict[str, Any]:
        db = getattr(context, "db_session", None)
        if not db:
            return {"success": False, "error": "Sessão de banco indisponível."}

        repo = InstagramRepository(db)
        limit = kwargs.get("limit", 10)
        pubs = repo.list_publications(context.user_id, limit=limit, offset=0)

        results = [
            {
                "id": p.id,
                "media_type": p.media_type,
                "caption_snippet": p.caption[:80] + "..." if len(p.caption) > 80 else p.caption,
                "status": p.publication_status,
                "instagram_media_id": p.instagram_media_id,
                "instagram_url": f"https://www.instagram.com/p/{p.instagram_media_id}/" if p.instagram_media_id else None,
                "published_at": p.published_at.isoformat() if p.published_at else None,
            }
            for p in pubs
        ]

        return {
            "success": True,
            "total": len(results),
            "publications": results,
        }
