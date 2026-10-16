from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Conversation, Message
from app.models.enums import MessageRole


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(stmt))

    def get_for_user(self, conversation_id: int, user_id: int) -> Conversation | None:
        stmt = select(Conversation).where(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        )
        return self.db.scalar(stmt)

    def create(self, user_id: int, title: str) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def rename(self, conversation: Conversation, title: str) -> Conversation:
        conversation.title = title
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def delete(self, conversation: Conversation) -> None:
        self.db.delete(conversation)
        self.db.commit()

    def recent_messages(self, conversation_id: int, limit: int) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(limit)
        )
        return list(reversed(list(self.db.scalars(stmt))))

    def add_exchange(
        self,
        conversation: Conversation,
        user_content: str,
        assistant_content: str,
        provider_steps: list[dict] | None,
        new_title: str | None = None,
    ) -> tuple[Message, Message]:
        """Grava a pergunta e a resposta juntas, numa única transação."""
        user_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=user_content,
        )
        assistant_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=assistant_content,
            provider_steps=provider_steps,
        )
        self.db.add_all([user_message, assistant_message])
        if new_title:
            conversation.title = new_title
        conversation.updated_at = func.now()
        self.db.commit()
        self.db.refresh(user_message)
        self.db.refresh(assistant_message)
        return user_message, assistant_message