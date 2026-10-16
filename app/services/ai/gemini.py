import logging
from functools import lru_cache

from google import genai

from app.core.config import settings
from app.services.ai.base import AIProviderError, AIReply, ChatTurn

logger = logging.getLogger(__name__)


@lru_cache
def _client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


class GeminiProvider:
    def generate(
        self, history: list[ChatTurn], system_instruction: str | None = None
    ) -> AIReply:
        steps: list[dict] = []
        for turn in history:
            if turn.role == "user":
                steps.append(
                    {"type": "user_input", "content": [{"type": "text", "text": turn.content}]}
                )
            elif turn.provider_steps:
                # Passos do modelo reenviados exatamente como vieram.
                steps.extend(turn.provider_steps)
            else:
                steps.append(
                    {"type": "model_output", "content": [{"type": "text", "text": turn.content}]}
                )

        params: dict = {"model": settings.gemini_model, "input": steps, "store": False}
        if system_instruction:
            params["system_instruction"] = system_instruction
        if settings.gemini_thinking_level:
            params["generation_config"] = {"thinking_level": settings.gemini_thinking_level}

        try:
            interaction = _client().interactions.create(**params)
        except Exception as exc:
            logger.exception("Falha na chamada ao Gemini")
            raise AIProviderError(str(exc)) from exc

        text = interaction.output_text
        if not text:
            raise AIProviderError("O Gemini devolveu uma resposta vazia")

        return AIReply(
            text=text,
            provider_steps=[step.model_dump(mode="json") for step in interaction.steps],
        )