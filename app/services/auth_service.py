from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import Token
from app.schemas.user import UserCreate

# Usado quando o e-mail não existe, para o tempo de resposta
# não revelar se o e-mail está cadastrado.
_DUMMY_HASH = hash_password("senha-falsa-para-tempo-constante")


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

    def login(self, email: str, password: str) -> Token:
        user = self.users.get_by_email(email.lower())
        hashed = user.password_hash if user else _DUMMY_HASH
        password_ok = verify_password(password, hashed)

        if not user or not password_ok:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha incorretos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return Token(access_token=create_access_token(user.id))

    @staticmethod
    def _email_conflict() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado",
        )