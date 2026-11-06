from dataclasses import dataclass
from typing import Any


@dataclass
class AgentContext:
    """Contexto de execução do agente, amarrado à sessão autenticada do usuário.
    
    Garante que ferramentas e operações só acessem recursos autorizados
    para este usuário específico.
    """
    user_id: int
    user_name: str
    conversation_id: int
    custom_instructions: str | None = None
    extra_metadata: dict[str, Any] | None = None
    db_session: Any | None = None

