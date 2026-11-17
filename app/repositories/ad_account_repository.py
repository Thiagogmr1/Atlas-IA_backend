from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AdAccount


class AdAccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user(self, user_id: int) -> list[AdAccount]:
        stmt = (
            select(AdAccount)
            .where(AdAccount.user_id == user_id)
            .order_by(AdAccount.connected_at.desc())
        )
        return list(self.db.scalars(stmt))

    def get_for_user(self, account_id: int, user_id: int) -> AdAccount | None:
        stmt = select(AdAccount).where(
            AdAccount.id == account_id, AdAccount.user_id == user_id
        )
        return self.db.scalar(stmt)

    def create(self, user_id: int, **fields) -> AdAccount:
        account = AdAccount(user_id=user_id, **fields)
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def delete(self, account: AdAccount) -> None:
        self.db.delete(account)
        self.db.commit()