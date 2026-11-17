from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.repositories.user_repository import UserRepository
from app.routers.deps import get_current_user
from app.schemas.user import AccountDeletionRequest, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def get_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserRead)
def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_service),
):
    return service.update_profile(current_user, data)


@router.post("/me/deletion", response_model=UserRead)
def request_account_deletion(
    data: AccountDeletionRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_service),
):
    return service.request_deletion(current_user, data.password)