from sqlalchemy import select
from sqlalchemy.orm import configure_mappers

from app import models
from app.core.database import SessionLocal

configure_mappers()

with SessionLocal() as db:
    for model in (
        models.User,
        models.AdAccount,
        models.Campaign,
        models.OptimizationRule,
        models.Ad,
        models.Metric,
        models.Creative,
        models.AgentActionLog,
    ):
        db.execute(select(model).limit(1)).first()
        print(f"OK  {model.__tablename__}")