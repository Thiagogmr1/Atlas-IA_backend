from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models import AdAccount
from app.repositories.ad_account_repository import AdAccountRepository
from app.schemas.ad_account import AdAccountCreate


class AdAccountService:
    def __init__(self, accounts: AdAccountRepository):
        self.accounts = accounts

    def list(self, user_id: int) -> list[AdAccount]:
        return self.accounts.list_by_user(user_id)

    def get(self, account_id: int, user_id: int) -> AdAccount:
        account = self.accounts.get_for_user(account_id, user_id)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conta de anúncio não encontrada",
            )
        return account

    def create(self, user_id: int, data: AdAccountCreate) -> AdAccount:
        try:
            return self.accounts.create(user_id, **data.model_dump())
        except IntegrityError:
            self.accounts.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta conta já está conectada",
            )

    def delete(self, account_id: int, user_id: int) -> None:
        account = self.get(account_id, user_id)
        self.accounts.delete(account)