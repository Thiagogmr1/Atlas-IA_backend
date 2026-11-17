from datetime import datetime
import logging
from typing import Any, List, Optional
import httpx
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class InstagramPostPayload(BaseModel):
    """Payload estruturado e validado para publicação no Instagram."""
    caption: str = Field(..., max_length=2200, description="Legenda do post (máx 2200 caracteres)")
    media_type: str = Field(..., description="IMAGE, VIDEO, REELS ou CAROUSEL")
    media_urls: List[str] = Field(..., min_length=1, description="Lista de URLs de mídia acessíveis")
    hashtags: Optional[List[str]] = Field(default=None, description="Hashtags adicionais")
    scheduled_for: Optional[datetime] = Field(default=None, description="Data/hora agendada (ISO)")
    location_tag: Optional[str] = Field(default=None, description="Nome do local marcado")

    @field_validator("media_type")
    @classmethod
    def validate_media_type(cls, v: str) -> str:
        upper = v.upper()
        if upper not in {"IMAGE", "VIDEO", "REELS", "CAROUSEL"}:
            raise ValueError("media_type deve ser 'IMAGE', 'VIDEO', 'REELS' ou 'CAROUSEL'")
        return upper

    @field_validator("hashtags")
    @classmethod
    def validate_hashtag_count(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v and len(v) > 30:
            raise ValueError("O Instagram permite no máximo 30 hashtags por post.")
        return v


class InstagramIntegration:
    """Módulo de integração real com Instagram Graph API (preparação, validação e publicação)."""

    MAX_CAPTION_LENGTH = 2200
    MAX_HASHTAGS = 30
    VALID_ASPECT_RATIOS = ["1:1", "4:5", "9:16", "16:9"]

    def __init__(self, http_client: httpx.Client | None = None):
        self.http_client = http_client or httpx.Client(timeout=30.0)

    def validate_post(self, payload: InstagramPostPayload) -> dict[str, Any]:
        """Valida se o post atende a todos os requisitos técnicos do Instagram."""
        issues: list[str] = []

        total_length = len(payload.caption)
        if payload.hashtags:
            total_length += sum(len(tag) + 2 for tag in payload.hashtags)

        if total_length > self.MAX_CAPTION_LENGTH:
            issues.append(
                f"Legenda excede o limite do Instagram ({total_length}/{self.MAX_CAPTION_LENGTH} caracteres)."
            )

        if payload.media_type == "CAROUSEL" and len(payload.media_urls) < 2:
            issues.append("Carrossel requer no mínimo 2 itens de mídia.")
        elif payload.media_type == "CAROUSEL" and len(payload.media_urls) > 10:
            issues.append("Carrossel suporta no máximo 10 itens de mídia.")

        is_valid = len(issues) == 0

        # Formata legenda final mesclando hashtags se fornecidas separadamente
        final_caption = payload.caption.strip()
        if payload.hashtags:
            clean_tags = [
                tag if tag.startswith("#") else f"#{tag}"
                for tag in payload.hashtags
            ]
            final_caption = f"{final_caption}\n\n{' '.join(clean_tags)}"

        return {
            "valid": is_valid,
            "issues": issues,
            "media_type": payload.media_type,
            "media_count": len(payload.media_urls),
            "media_urls": payload.media_urls,
            "final_caption": final_caption,
            "char_count": len(final_caption),
            "scheduled_for": payload.scheduled_for.isoformat() if payload.scheduled_for else None,
            "status": "ready_for_review" if is_valid else "validation_failed",
            "future_meta_graph_api_ready": True,
        }

    def publish_to_instagram(
        self,
        access_token: str,
        ig_user_id: str,
        payload: InstagramPostPayload,
    ) -> dict[str, Any]:
        """Executa a publicação real via Instagram Graph API.
        
        NUNCA simula: faz a chamada HTTP autêntica e só confirma sucesso
        após retorno positivo dos servidores da Meta.
        """
        # 1. Validação prévia estrita
        validation = self.validate_post(payload)
        if not validation["valid"]:
            return {
                "success": False,
                "error": "Falha na validação técnica do post",
                "issues": validation["issues"],
            }

        final_caption = validation["final_caption"]
        media_type = payload.media_type.upper()

        try:
            # Caso 1: Publicação de Foto Única
            if media_type == "IMAGE":
                container_resp = self.http_client.post(
                    f"{GRAPH_API_BASE_URL}/{ig_user_id}/media",
                    data={
                        "image_url": payload.media_urls[0],
                        "caption": final_caption,
                        "access_token": access_token,
                    },
                )
                container_data = container_resp.json()
                if container_resp.status_code != 200 or "id" not in container_data:
                    err_msg = container_data.get("error", {}).get("message", "Erro ao criar contêiner de imagem no Instagram")
                    return {"success": False, "error": err_msg, "status_code": container_resp.status_code}

                creation_id = container_data["id"]

            # Caso 2: Publicação de Vídeo ou Reels
            elif media_type in {"VIDEO", "REELS"}:
                container_resp = self.http_client.post(
                    f"{GRAPH_API_BASE_URL}/{ig_user_id}/media",
                    data={
                        "media_type": "REELS",
                        "video_url": payload.media_urls[0],
                        "caption": final_caption,
                        "access_token": access_token,
                    },
                )
                container_data = container_resp.json()
                if container_resp.status_code != 200 or "id" not in container_data:
                    err_msg = container_data.get("error", {}).get("message", "Erro ao criar contêiner de Reels no Instagram")
                    return {"success": False, "error": err_msg, "status_code": container_resp.status_code}

                creation_id = container_data["id"]

            # Caso 3: Publicação de Carrossel
            elif media_type == "CAROUSEL":
                item_ids = []
                for item_url in payload.media_urls:
                    item_resp = self.http_client.post(
                        f"{GRAPH_API_BASE_URL}/{ig_user_id}/media",
                        data={
                            "is_carousel_item": "true",
                            "image_url": item_url,
                            "access_token": access_token,
                        },
                    )
                    item_data = item_resp.json()
                    if item_resp.status_code != 200 or "id" not in item_data:
                        return {
                            "success": False,
                            "error": f"Erro ao criar item do carrossel ({item_url}): {item_data.get('error', {}).get('message')}",
                        }
                    item_ids.append(item_data["id"])

                carousel_resp = self.http_client.post(
                    f"{GRAPH_API_BASE_URL}/{ig_user_id}/media",
                    data={
                        "media_type": "CAROUSEL",
                        "children": ",".join(item_ids),
                        "caption": final_caption,
                        "access_token": access_token,
                    },
                )
                carousel_data = carousel_resp.json()
                if carousel_resp.status_code != 200 or "id" not in carousel_data:
                    return {"success": False, "error": carousel_data.get("error", {}).get("message", "Erro no carrossel")}
                creation_id = carousel_data["id"]
            else:
                return {"success": False, "error": f"Tipo de mídia não suportado: {media_type}"}

            # Passo Final: Publicação do Contêiner
            publish_resp = self.http_client.post(
                f"{GRAPH_API_BASE_URL}/{ig_user_id}/media_publish",
                data={
                    "creation_id": creation_id,
                    "access_token": access_token,
                },
            )
            publish_data = publish_resp.json()

            if publish_resp.status_code == 200 and "id" in publish_data:
                published_media_id = publish_data["id"]
                logger.info("Publicação confirmada no Instagram. Media ID: %s", published_media_id)
                return {
                    "success": True,
                    "published_media_id": published_media_id,
                    "instagram_post_url": f"https://www.instagram.com/p/{published_media_id}/",
                    "status": "published",
                    "published_at": datetime.now().isoformat(),
                }
            else:
                err_msg = publish_data.get("error", {}).get("message", "Falha ao publicar contêiner no Instagram")
                return {"success": False, "error": err_msg, "status_code": publish_resp.status_code}

        except Exception as exc:
            logger.error("Exceção na comunicação com Instagram Graph API: %s", exc.__class__.__name__)
            return {"success": False, "error": f"Erro de comunicação com Instagram API: {str(exc)}"}
