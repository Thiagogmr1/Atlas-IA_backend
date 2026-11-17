from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field

from app.core.config import settings


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    last_name: str | None = Field(default=None, max_length=150)
    email: EmailStr | None = None
    custom_instructions: str | None = Field(default=None, max_length=4000)


class AccountDeletionRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    last_name: str | None
    email: EmailStr
    custom_instructions: str | None
    deletion_requested_at: datetime | None
    created_at: datetime

    @computed_field
    @property
    def deletion_scheduled_for(self) -> datetime | None:
        """Data em que os dados serão apagados, se a exclusão foi solicitada."""
        if self.deletion_requested_at is None:
            return None
        return self.deletion_requested_at + timedelta(
            days=settings.account_deletion_grace_days
        )