from abc import ABC, abstractmethod
from typing import Any, Type

from google.genai import types
from pydantic import BaseModel, ValidationError

from app.agent.context import AgentContext


class AgentTool(ABC):
    """Classe base para todas as ferramentas do agente AtlasAI.
    
    Cada ferramenta deve definir:
    - name: nome da função (snake_case)
    - description: descrição clara do propósito para o Gemini
    - args_schema: classe Pydantic que valida os argumentos de entrada
    """

    name: str
    description: str
    args_schema: Type[BaseModel]

    @abstractmethod
    def execute(self, context: AgentContext, **kwargs) -> dict[str, Any]:
        """Executa a lógica da ferramenta com os argumentos já validados."""
        pass

    def validate_and_execute(
        self, context: AgentContext, raw_args: dict[str, Any]
    ) -> dict[str, Any]:
        """Valida os argumentos recebidos do LLM via Pydantic e executa a ferramenta.
        
        Trata erros de validação sem vazar dados sensíveis, retornando uma mensagem
        estruturada para que o modelo possa se autocorrigir se necessário.
        """
        try:
            validated = self.args_schema(**raw_args)
            return self.execute(context, **validated.model_dump())
        except ValidationError as val_err:
            return {
                "success": False,
                "error": "Parâmetros inválidos para a ferramenta",
                "details": [
                    {"field": " -> ".join(str(loc) for loc in err["loc"]), "msg": err["msg"]}
                    for err in val_err.errors()
                ],
            }
        except Exception as exc:
            return {
                "success": False,
                "error": f"Falha na execução da ferramenta {self.name}: {str(exc)}",
            }

    def to_function_declaration(self) -> types.FunctionDeclaration:
        """Converte a ferramenta para a declaração de função do SDK Gemini."""
        schema = self.args_schema.model_json_schema()
        # Remove títulos que não agregam para a interpretação do LLM
        schema.pop("title", None)
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters_json_schema=schema,
        )

