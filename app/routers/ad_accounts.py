from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.repositories.ad_account_repository import AdAccountRepository
from app.routers.deps import get_current_user
from app.schemas.ad_account import AdAccountCreate, AdAccountRead
from app.services.ad_account_service import AdAccountService

router = APIRouter(prefix="/ad-accounts", tags=["Ad Accounts"])


def get_service(db: Session = Depends(get_db)) -> AdAccountService:
    return AdAccountService(AdAccountRepository(db))


@router.post("", response_model=AdAccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    data: AdAccountCreate,
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_service),
):
    return service.create(current_user.id, data)


@router.get("", response_model=list[AdAccountRead])
def list_accounts(
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_service),
):
    return service.list(current_user.id)


@router.get("/{account_id}", response_model=AdAccountRead)
def get_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_service),
):
    return service.get(account_id, current_user.id)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_service),
):
    service.delete(account_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)