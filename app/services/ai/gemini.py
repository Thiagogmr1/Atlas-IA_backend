import logging
from typing import TYPE_CHECKING

from app.agent.context import AgentContext
from app.services.ai.base import AIProvider, AIProviderError, AIReply, ChatTurn

if TYPE_CHECKING:
    from app.agent.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)


class GeminiProvider(AIProvider):
    """Provedor Gemini integrado ao AgentOrchestrator com Function Calling e segurança."""

    def __init__(self, orchestrator: "AgentOrchestrator | None" = None):
        if orchestrator is None:
            from app.agent.orchestrator import AgentOrchestrator
            orchestrator = AgentOrchestrator()
        self.orchestrator = orchestrator

    def generate(
        self, history: list[ChatTurn], system_instruction: str | None = None
    ) -> AIReply:
        """Compatibilidade com o protocolo AIProvider."""
        if not history:
            return AIReply(text="")

        turns = history[:-1]
        last_turn = history[-1]

        context = AgentContext(
            user_id=0,
            user_name="Usuario",
            conversation_id=0,
            custom_instructions=system_instruction,
        )

        return self.orchestrator.run(
            history=turns,
            new_message=last_turn.content,
            context=context,
        )

    def generate_with_context(
        self,
        history: list[ChatTurn],
        new_message: str,
        context: AgentContext,
    ) -> AIReply:
        """Executa a interação completa fornecendo o contexto autenticado do usuário."""
        return self.orchestrator.run(
            history=history,
            new_message=new_message,
            context=context,
        )
