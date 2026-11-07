from datetime import datetime, timezone
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models import Conversation, Message, User
from app.models.enums import MessageRole
from app.routers.deps import get_current_user
from app.services.ai.base import AIReply
from app.services.chat_service import ChatService


def test_api_send_message_endpoint():
    client = TestClient(app)

    # Cria usuário e mock de repositório
    user = User(id=1, name="Gabriel", email="gabriel@atlasai.com", custom_instructions=None)
    conversation = Conversation(id=10, user_id=1, title="Nova conversa")

    mock_db = MagicMock()
    mock_repo = MagicMock()
    mock_repo.get_for_user.return_value = conversation
    mock_repo.recent_messages.return_value = []

    now = datetime.now(timezone.utc)
    user_msg = Message(id=101, conversation_id=10, role=MessageRole.USER, content="Quero uma estratégia de vendas", created_at=now)
    assistant_msg = Message(
        id=102,
        conversation_id=10,
        role=MessageRole.ASSISTANT,
        content="Aqui está sua estratégia com base no objetivo de vendas.",
        provider_steps=[{"type": "function_call", "name": "analyze_marketing_goal"}],
        created_at=now,
    )
    mock_repo.add_exchange.return_value = (user_msg, assistant_msg)

    mock_ai = MagicMock()
    mock_ai.generate_with_context.return_value = AIReply(
        text="Aqui está sua estratégia com base no objetivo de vendas.",
        provider_steps=[{"type": "function_call", "name": "analyze_marketing_goal"}],
    )

    fake_service = ChatService(conversations=mock_repo, ai=mock_ai)

    # Overrides de dependências para o teste
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    from app.routers.conversations import get_service
    app.dependency_overrides[get_service] = lambda: fake_service

    try:
        response = client.post(
            "/conversations/10/messages",
            json={"content": "Quero uma estratégia de vendas"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_message"]["content"] == "Quero uma estratégia de vendas"
        assert data["assistant_message"]["content"] == "Aqui está sua estratégia com base no objetivo de vendas."
        # Garante que chaves ou segredos não estão no payload retornado
        assert "gemini_api_key" not in str(data)
        assert "AIza" not in str(data)
    finally:
        app.dependency_overrides.clear()


def test_api_unauthorized_user_cannot_access_other_conversation():
    client = TestClient(app)
    user = User(id=2, name="Hacker", email="hacker@test.com")

    mock_db = MagicMock()
    mock_repo = MagicMock()
    # Conversa ID 10 pertence ao user 1, então para o user 2 retorna None
    mock_repo.get_for_user.return_value = None
    fake_service = ChatService(conversations=mock_repo, ai=MagicMock())

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    from app.routers.conversations import get_service
    app.dependency_overrides[get_service] = lambda: fake_service

    try:
        response = client.get("/conversations/10")
        assert response.status_code == 404
        assert response.json()["detail"] == "Conversa não encontrada"
    finally:
        app.dependency_overrides.clear()


def test_api_upload_media_endpoint():
    import io
    from PIL import Image

    client = TestClient(app)
    user = User(id=1, name="Gabriel", email="gabriel@atlasai.com")
    conversation = Conversation(id=10, user_id=1, title="Nova conversa")

    mock_db = MagicMock()
    mock_repo = MagicMock()
    mock_repo.get_for_user.return_value = conversation
    fake_service = ChatService(conversations=mock_repo, ai=MagicMock())

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    from app.routers.conversations import get_service
    app.dependency_overrides[get_service] = lambda: fake_service

    buf = io.BytesIO()
    img = Image.new("RGB", (30, 30), color="green")
    img.save(buf, format="JPEG")
    jpeg_bytes = buf.getvalue()

    try:
        response = client.post(
            "/conversations/10/upload",
            files={"file": ("test_perfume.jpg", jpeg_bytes, "image/jpeg")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["media_kind"] == "image"
        assert "/media/users/1/" in data["media_url"]
        assert data["content_type"] == "image/jpeg"
    finally:
        app.dependency_overrides.clear()
