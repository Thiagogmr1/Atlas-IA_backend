from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass
class ChatTurn:
    role: Literal["user", "assistant"]
    content: str
    provider_steps: list[dict] | None = None


@dataclass
class AIReply:
    text: str
    provider_steps: list[dict] | None = None


class AIProviderError(Exception):
    """Falha ao obter a resposta do provedor de IA."""


class AIProvider(Protocol):
    def generate(
        self, history: list[ChatTurn], system_instruction: str | None = None
    ) -> AIReply: ...