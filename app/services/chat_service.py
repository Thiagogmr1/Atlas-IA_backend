from fastapi import HTTPException, status

from app.core.config import settings
from app.models import Conversation, Message, User
from app.models.enums import MessageRole
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.conversation import ConversationCreate, ConversationUpdate, MessageCreate
from app.services.ai import AIProvider, AIProviderError, ChatTurn

DEFAULT_TITLE = "Nova conversa"
AUTO_TITLE_MAX = 60


def _auto_title(text: str) -> str:
    first_line = text.strip().splitlines()[0]
    if len(first_line) <= AUTO_TITLE_MAX:
        return first_line
    return first_line[: AUTO_TITLE_MAX - 1].rstrip() + "…"


class ChatService:
    def __init__(self, conversations: ConversationRepository, ai: AIProvider):
        self.conversations = conversations
        self.ai = ai

    def list(self, user_id: int, limit: int, offset: int) -> list[Conversation]:
        return self.conversations.list_by_user(user_id, limit, offset)

    def get(self, conversation_id: int, user_id: int) -> Conversation:
        conversation = self.conversations.get_for_user(conversation_id, user_id)
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversa não encontrada",
            )
        return conversation

    def create(self, user_id: int, data: ConversationCreate) -> Conversation:
        title = (data.title or "").strip() or DEFAULT_TITLE
        return self.conversations.create(user_id, title)

    def rename(
        self, conversation_id: int, user_id: int, data: ConversationUpdate
    ) -> Conversation:
        conversation = self.get(conversation_id, user_id)
        title = data.title.strip()
        if not title:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="O título não pode ficar vazio",
            )
        return self.conversations.rename(conversation, title)

    def delete(self, conversation_id: int, user_id: int) -> None:
        conversation = self.get(conversation_id, user_id)
        self.conversations.delete(conversation)

    def send_message(
        self, conversation_id: int, user: User, data: MessageCreate
    ) -> tuple[Message, Message]:
        conversation = self.get(conversation_id, user.id)

        recent = self.conversations.recent_messages(
            conversation.id, settings.chat_history_limit
        )
        is_first_message = not recent

        # O histórico enviado à IA precisa começar por uma mensagem do usuário.
        history = list(recent)
        while history and history[0].role == MessageRole.ASSISTANT:
            history.pop(0)

        turns = [
            ChatTurn(
                role=m.role.value, content=m.content, provider_steps=m.provider_steps
            )
            for m in history
        ]
        turns.append(ChatTurn(role="user", content=data.content))

        try:
            reply = self.ai.generate(turns, system_instruction=user.custom_instructions)
        except AIProviderError:
            # Nada é gravado se a IA falhar: o usuário só reenvia a mensagem.
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Não foi possível obter a resposta da IA agora. Tente novamente em instantes.",
            )

        new_title = None
        if is_first_message and conversation.title == DEFAULT_TITLE:
            new_title = _auto_title(data.content)

        return self.conversations.add_exchange(
            conversation,
            user_content=data.content,
            assistant_content=reply.text,
            provider_steps=reply.provider_steps,
            new_title=new_title,
        )