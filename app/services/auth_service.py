from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, users: UserRepository):
        self.users = users

    def register(self, data: UserCreate) -> User:
        email = data.email.lower()

        if self.users.get_by_email(email):
            raise self._email_conflict()

        try:
            return self.users.create(
                name=data.name.strip(),
                email=email,
                password_hash=hash_password(data.password),
            )
        except IntegrityError:
            self.users.db.rollback()
            raise self._email_conflict()

    @staticmethod
    def _email_conflict() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado",
        )