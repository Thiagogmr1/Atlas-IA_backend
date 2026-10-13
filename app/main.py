from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.routers import ad_accounts, auth, users

app = FastAPI(title="AtlasAI API")
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ad_accounts.router)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}