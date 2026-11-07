from unittest.mock import MagicMock
import pytest
from fastapi import HTTPException

from app.models import Conversation, Message, User
from app.models.enums import MessageRole
from app.schemas.conversation import ConversationCreate, ConversationUpdate, MessageCreate
from app.services.ai.base import AIReply
from app.services.chat_service import ChatService


def test_user_cannot_access_other_user_conversation():
    mock_repo = MagicMock()
    # Retorna None porque a conversa pertence a outro user_id
    mock_repo.get_for_user.return_value = None
    mock_ai = MagicMock()

    service = ChatService(conversations=mock_repo, ai=mock_ai)

    with pytest.raises(HTTPException) as exc_info:
        service.get(conversation_id=99, user_id=1)

    assert exc_info.value.status_code == 404
    assert "Conversa não encontrada" in exc_info.value.detail


def test_send_message_invokes_ai_with_user_context():
    mock_repo = MagicMock()
    user = User(id=7, name="Roberta", email="roberta@example.com", custom_instructions="Tom amigável")
    conversation = Conversation(id=10, user_id=7, title="Nova conversa")

    mock_repo.get_for_user.return_value = conversation
    mock_repo.recent_messages.return_value = []

    mock_ai = MagicMock()
    mock_ai.generate_with_context.return_value = AIReply(
        text="Olá Roberta! Vamos criar sua estratégia.",
        provider_steps=[{"type": "function_call", "name": "analyze_marketing_goal"}],
    )

    # Simula retorno do banco para o exchange
    user_msg = Message(id=1, conversation_id=10, role=MessageRole.USER, content="Quero vender mais")
    assistant_msg = Message(
        id=2,
        conversation_id=10,
        role=MessageRole.ASSISTANT,
        content="Olá Roberta! Vamos criar sua estratégia.",
        provider_steps=[{"type": "function_call", "name": "analyze_marketing_goal"}],
    )
    mock_repo.add_exchange.return_value = (user_msg, assistant_msg)

    service = ChatService(conversations=mock_repo, ai=mock_ai)
    u_ret, a_ret = service.send_message(10, user, MessageCreate(content="Quero vender mais"))

    # Verifica se chamou a IA com o contexto contendo o user_id correto
    mock_ai.generate_with_context.assert_called_once()
    _, kwargs = mock_ai.generate_with_context.call_args
    assert kwargs["context"].user_id == 7
    assert kwargs["context"].user_name == "Roberta"
    assert kwargs["context"].conversation_id == 10
    assert kwargs["context"].custom_instructions == "Tom amigável"

    # Verifica se gravou com o novo título na primeira mensagem
    mock_repo.add_exchange.assert_called_once()
    call_kwargs = mock_repo.add_exchange.call_args.kwargs
    assert call_kwargs["new_title"] == "Quero vender mais"
    assert call_kwargs["provider_steps"] == [{"type": "function_call", "name": "analyze_marketing_goal"}]


def test_list_conversations_filters_strictly_by_user():
    mock_repo = MagicMock()
    mock_repo.list_by_user.return_value = [Conversation(id=1, user_id=42, title="Conversa 1")]
    mock_ai = MagicMock()

    service = ChatService(conversations=mock_repo, ai=mock_ai)
    result = service.list(user_id=42, limit=50, offset=0)

    mock_repo.list_by_user.assert_called_once_with(42, 50, 0)
    assert len(result) == 1
    assert result[0].user_id == 42

