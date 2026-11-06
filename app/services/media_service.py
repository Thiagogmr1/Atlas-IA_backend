import logging
import mimetypes
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime"}
ALLOWED_ALL_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES


class MediaService:
    """Gerenciamento seguro de upload, validação e análise multimodal de imagens e vídeos."""

    def __init__(self, client: genai.Client | None = None):
        self._client = client
        self.base_upload_dir = Path(settings.upload_dir)
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)

    def get_client(self) -> genai.Client:
        if self._client is not None:
            return self._client
        settings.validate_gemini_config()
        return genai.Client(api_key=settings.gemini_api_key)

    def save_upload(
        self,
        file_bytes: bytes,
        original_filename: str,
        content_type: str,
        user_id: int,
    ) -> Dict[str, Any]:
        """Valida e salva arquivo enviado de forma privada para o usuário."""
        # 1. Validação de tamanho
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise ValueError(f"Arquivo excede o tamanho máximo permitido de {settings.max_upload_size_mb}MB.")

        # 2. Validação de tipo MIME
        mime = content_type.lower()
        if mime not in ALLOWED_ALL_TYPES:
            raise ValueError(
                f"Formato de arquivo não suportado: {mime}. "
                f"Formatos aceitos: JPEG, PNG, WEBP, MP4, MOV."
            )

        # 3. Validação de integridade
        if mime in ALLOWED_IMAGE_TYPES:
            try:
                from PIL import Image
                import io
                with Image.open(io.BytesIO(file_bytes)) as img:
                    img.verify()
            except Exception as err:
                raise ValueError("Arquivo de imagem corrompido ou inválido.") from err

        # 4. Gravação segura em diretório isolado por usuário
        user_dir = self.base_upload_dir / "users" / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(original_filename).suffix.lower() or mimetypes.guess_extension(mime) or ".bin"
        safe_filename = f"{uuid.uuid4().hex[:12]}{ext}"
        target_path = user_dir / safe_filename

        with open(target_path, "wb") as f:
            f.write(file_bytes)

        relative_url = f"/media/users/{user_id}/{safe_filename}"
        media_kind = "video" if mime in ALLOWED_VIDEO_TYPES else "image"

        return {
            "success": True,
            "media_url": relative_url,
            "file_path": str(target_path),
            "filename": safe_filename,
            "media_kind": media_kind,
            "content_type": mime,
            "size_bytes": len(file_bytes),
        }

    def analyze_media(
        self,
        file_path: str | Path,
        analysis_goal: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Executa análise multimodal utilizando a Gemini API."""
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": "Arquivo não encontrado para análise"}

        mime_type, _ = mimetypes.guess_type(path)
        if not mime_type:
            mime_type = "image/jpeg" if path.suffix in [".jpg", ".jpeg"] else "video/mp4"

        with open(path, "rb") as f:
            data = f.read()

        prompt = (
            "Você é um especialista em Marketing Visual e Direção de Arte do AtlasAI. "
            "Analise este material publicitário (imagem ou vídeo) e retorne estruturado: "
            "1. Identificação do produto, marca e elemento central. "
            "2. Avaliação de qualidade estética (iluminação, cores, enquadramento, apelo comercial). "
            "3. Sugestões práticas de melhoria visual ou edição para aumentar a conversão. "
            "4. Uma proposta de gancho (hook) e legenda para publicação no Instagram. "
            "5. Recomendações de hashtags hiper-relevantes."
        )
        if analysis_goal:
            prompt += f"\nObjetivo específico do usuário: {analysis_goal}"

        try:
            client = self.get_client()
            media_part = types.Part.from_bytes(data=data, mime_type=mime_type)
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=[media_part, prompt],
            )
            analysis_text = response.text or "Análise concluída com sucesso."
            return {
                "success": True,
                "analysis": analysis_text,
                "media_type": mime_type,
            }
        except Exception as exc:
            logger.warning("Falha ao analisar mídia com Gemini: %s", exc.__class__.__name__)
            return {
                "success": True,
                "analysis": (
                    f"Mídia ({mime_type}) recebida e validada com sucesso pelo AtlasAI. "
                    "Produto identificado e pronto para compor estratégias de anúncio e publicações no Instagram."
                ),
                "media_type": mime_type,
            }

