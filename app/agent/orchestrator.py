import logging
from typing import Any, List

from google import genai
from google.genai import types

from app.agent.context import AgentContext
from app.agent.prompts import build_system_instruction
from app.core.config import settings
from app.security.guardrails import (
    detect_prompt_injection,
    sanitize_input,
    sanitize_output,
)
from app.services.ai.base import AIProviderError, AIReply, ChatTurn
from app.tools.registry import ToolRegistry, default_registry

logger = logging.getLogger(__name__)

MAX_TOOL_TURNS = 5


class AgentOrchestrator:
    """Orquestrador do Agente de IA do AtlasAI.
    
    Responsabilidades:
    - Autenticação e isolamento do contexto do usuário.
    - Proteção ativa contra prompt injection e extração de credenciais.
    - Ciclo de Function Calling (pergunta -> Gemini -> ferramentas -> resposta final).
    - Validação de parâmetros e permissões de execução.
    - Higienização e mascaramento de segredos na saída.
    """

    def __init__(self, tool_registry: ToolRegistry | None = None, client: genai.Client | None = None):
        self.tools = tool_registry or default_registry
        self._client = client

    def get_client(self) -> genai.Client:
        if self._client is not None:
            return self._client
        settings.validate_gemini_config()
        return genai.Client(api_key=settings.gemini_api_key)

    def run(
        self,
        history: List[ChatTurn],
        new_message: str,
        context: AgentContext,
    ) -> AIReply:
        """Executa a interação completa do agente com segurança e Function Calling."""
        # 1. Higienização e validação de entrada
        cleaned_input = sanitize_input(new_message)

        # 2. Defesa contra Prompt Injection e Extração de Credenciais
        if detect_prompt_injection(cleaned_input):
            logger.warning(
                "Tentativa de prompt injection ou extração detectada do usuário %s",
                context.user_id,
            )
            safe_refusal = (
                "Como especialista de marketing do AtlasAI, meu foco é exclusivamente planejar e "
                "otimizar suas campanhas, anúncios e estratégias de crescimento.\n\n"
                "Por políticas rigorosas de segurança, não forneço instruções de sistema, configurações internas "
                "ou credenciais de servidor. Como posso te apoiar com o marketing do seu negócio hoje?"
            )
            return AIReply(text=safe_refusal, provider_steps=[{"type": "security_guardrail", "action": "blocked_injection"}])

        # 3. Montagem do histórico para o modelo
        contents: list[types.Content] = []
        for turn in history:
            if turn.role == "user":
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=turn.content)],
                    )
                )
            elif turn.role == "assistant":
                contents.append(
                    types.Content(
                        role="model",
                        parts=[types.Part.from_text(text=turn.content)],
                    )
                )

        # Adiciona a mensagem atual do usuário
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=cleaned_input)],
            )
        )

        system_instruction = build_system_instruction(context.custom_instructions)
        gemini_tool = self.tools.to_gemini_tool()

        # Configuração da chamada Gemini
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[gemini_tool],
        )

        provider_steps: list[dict[str, Any]] = []
        final_text: str = ""

        try:
            client = self.get_client()
        except ValueError as val_err:
            logger.error("Configuração do Gemini inválida: %s", str(val_err))
            raise AIProviderError("O serviço de inteligência artificial não está devidamente configurado.")
        except Exception as exc:
            logger.error("Falha ao inicializar cliente Gemini: %s", exc.__class__.__name__)
            raise AIProviderError("Falha na autenticação do provedor de inteligência artificial.")

        # 4. Loop de Execução e Function Calling
        for iteration in range(MAX_TOOL_TURNS):
            try:
                response = client.models.generate_content(
                    model=settings.gemini_model,
                    contents=contents,
                    config=config,
                )
            except Exception as exc:
                # Log sanitizado (NUNCA loga chaves nem parâmetros confidenciais)
                logger.error(
                    "Erro ao chamar Gemini API (iteração %s): %s",
                    iteration,
                    exc.__class__.__name__,
                )
                raise AIProviderError("Não foi possível obter a resposta da IA. Tente novamente em instantes.")

            # Verifica se o modelo solicitou chamadas de ferramentas
            function_calls = getattr(response, "function_calls", None)

            if not function_calls:
                # Sem mais ferramentas pendentes: resposta final em texto
                candidate_text = response.text or ""
                final_text = candidate_text
                break

            # Se o modelo gerou chamadas de função, adiciona o conteúdo do modelo ao histórico
            if response.candidates and response.candidates[0].content:
                contents.append(response.candidates[0].content)

            # Executa cada ferramenta com validação estrita
            function_response_parts: list[types.Part] = []

            for call in function_calls:
                call_name = call.name
                call_args = call.args if hasattr(call, "args") and isinstance(call.args, dict) else {}

                logger.info("Executando ferramenta solicitada pelo Gemini: %s", call_name)

                # Executa com isolamento de contexto do usuário
                tool_output = self.tools.execute_tool(call_name, call_args, context)

                step_record = {
                    "type": "function_call",
                    "name": call_name,
                    "args": call_args,
                    "result": tool_output,
                }
                provider_steps.append(step_record)

                function_response_parts.append(
                    types.Part.from_function_response(
                        name=call_name,
                        response={"result": tool_output},
                    )
                )

            # Adiciona os resultados das ferramentas ao contexto da conversa
            contents.append(
                types.Content(
                    role="tool",
                    parts=function_response_parts,
                )
            )

        # Se atingiu o limite de turnos sem texto final, pede síntese ao modelo
        if not final_text:
            try:
                synthesis_config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                )
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text="Apresente uma resposta final detalhada para o usuário com base nos dados obtidos.")],
                    )
                )
                synthesis_resp = client.models.generate_content(
                    model=settings.gemini_model,
                    contents=contents,
                    config=synthesis_config,
                )
                final_text = synthesis_resp.text or "Operação concluída com sucesso."
            except Exception:
                final_text = "Operações executadas com sucesso. Verifique os detalhes retornados pelas ferramentas."

        # 5. Higienização da saída para evitar vazamento acidental de credenciais
        sanitized_final_text = sanitize_output(final_text)

        return AIReply(text=sanitized_final_text, provider_steps=provider_steps)

