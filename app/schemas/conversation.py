from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.models.enums import MessageRole


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)


class ConversationUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=150)


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    media_urls: Optional[List[str]] = Field(default=None, description="URLs de imagens ou vídeos anexados no chat")

    @field_validator("content")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("A mensagem não pode estar vazia")
        return value


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: MessageRole
    content: str
    provider_steps: Optional[list] = None
    created_at: datetime

    @computed_field
    @property
    def media_urls(self) -> Optional[List[str]]:
        if self.provider_steps:
            for step in self.provider_steps:
                if isinstance(step, dict) and step.get("type") == "user_attachment":
                    return step.get("media_urls")
        return None


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationRead):
    messages: list[MessageRead]


class ChatExchange(BaseModel):
    user_message: MessageRead
    assistant_message: MessageRead


class UploadResponse(BaseModel):
    media_url: str
    filename: str
    media_kind: str
    content_type: str
    size_bytes: int
