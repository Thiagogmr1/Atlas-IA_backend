from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.repositories.conversation_repository import ConversationRepository
from app.routers.deps import get_current_user
from app.schemas.conversation import (
    ChatExchange,
    ConversationCreate,
    ConversationDetail,
    ConversationRead,
    ConversationUpdate,
    MessageCreate,
)
from app.services.ai import get_ai_provider
from app.services.chat_service import ChatService

router = APIRouter(prefix="/conversations", tags=["Conversations"])


def get_service(db: Session = Depends(get_db)) -> ChatService:
    return ChatService(ConversationRepository(db), get_ai_provider())


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_service),
):
    return service.create(current_user.id, data)


@router.get("", response_model=list[ConversationRead])
def list_conversations(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_service),
):
    return service.list(current_user.id, limit, offset)


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_service),
):
    return service.get(conversation_id, current_user.id)


@router.patch("/{conversation_id}", response_model=ConversationRead)
def rename_conversation(
    conversation_id: int,
    data: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_service),
):
    return service.rename(conversation_id, current_user.id, data)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_service),
):
    service.delete(conversation_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{conversation_id}/messages",
    response_model=ChatExchange,
    status_code=status.HTTP_201_CREATED,
)
def send_message(
    conversation_id: int,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_service),
):
    user_message, assistant_message = service.send_message(
        conversation_id, current_user, data
    )
    return {"user_message": user_message, "assistant_message": assistant_message}