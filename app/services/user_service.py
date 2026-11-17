from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.security import verify_password
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdate


class UserService:
    def __init__(self, users: UserRepository):
        self.users = users

    def update_profile(self, user: User, data: UserUpdate) -> User:
        fields = data.model_dump(exclude_unset=True)

        # Colunas obrigatórias no banco não aceitam null.
        for key in ("name", "email"):
            if key in fields and fields[key] is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"O campo '{key}' não pode ser nulo",
                )

        if "name" in fields:
            fields["name"] = fields["name"].strip()

        # Texto vazio vira null, para limpar o campo.
        for key in ("last_name", "custom_instructions"):
            if key in fields and fields[key] is not None:
                fields[key] = fields[key].strip() or None

        if "email" in fields:
            email = fields["email"].lower()
            other = self.users.get_by_email(email)
            if other is not None and other.id != user.id:
                raise self._email_conflict()
            fields["email"] = email

        if not fields:
            return user

        try:
            return self.users.update(user, fields)
        except IntegrityError:
            self.users.db.rollback()
            raise self._email_conflict()

    def request_deletion(self, user: User, password: str) -> User:
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Senha incorreta",
            )
        if user.deletion_requested_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A exclusão desta conta já foi solicitada",
            )
        return self.users.set_deletion_requested(user, datetime.now(timezone.utc))

    @staticmethod
    def _email_conflict() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado",
        )