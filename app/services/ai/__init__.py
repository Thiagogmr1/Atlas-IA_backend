from app.services.ai.base import AIProvider, AIProviderError, AIReply, ChatTurn
from app.services.ai.gemini import GeminiProvider


def get_ai_provider() -> AIProvider:
    return GeminiProvider()


__all__ = ["AIProvider", "AIProviderError", "AIReply", "ChatTurn", "get_ai_provider"]