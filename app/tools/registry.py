import logging
from typing import Any, Dict

from google.genai import types

from app.agent.context import AgentContext
from app.security.permissions import validate_tool_allowed
from app.tools.base import AgentTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registro central de ferramentas disponíveis para o agente AtlasAI.
    
    Garante validação rígida de permissões e controle de execução.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, AgentTool] = {}

    def register(self, tool: AgentTool) -> None:
        """Registra uma nova ferramenta."""
        if tool.name in self._tools:
            logger.warning("Sobrescrevendo ferramenta existente: %s", tool.name)
        self._tools[tool.name] = tool

    def get(self, name: str) -> AgentTool | None:
        """Retorna uma ferramenta pelo nome."""
        return self._tools.get(name)

    def tool_names(self) -> set[str]:
        """Conjunto com o nome de todas as ferramentas registradas."""
        return set(self._tools.keys())

    def to_gemini_tool(self) -> types.Tool:
        """Exporta todas as ferramentas registradas como types.Tool do Gemini."""
        declarations = [tool.to_function_declaration() for tool in self._tools.values()]
        return types.Tool(function_declarations=declarations)

    def execute_tool(
        self, name: str, args: dict[str, Any], context: AgentContext
    ) -> dict[str, Any]:
        """Executa a ferramenta com validação de permissões e contexto seguro."""
        validate_tool_allowed(name, self.tool_names())
        tool = self._tools[name]
        logger.info(
            "Executando ferramenta %s para usuário %s (conversa %s)",
            name,
            context.user_id,
            context.conversation_id,
        )
        return tool.validate_and_execute(context, args)


default_registry = ToolRegistry()

