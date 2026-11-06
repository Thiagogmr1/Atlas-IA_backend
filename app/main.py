import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.routers import (
    ad_accounts,
    agent_actions,
    auth,
    campaigns,
    conversations,
    creatives,
    instagram,
    optimization_rules,
    users,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialização: validações de segurança e integridade do backend
    try:
        settings.validate_gemini_config()
        logger.info("AtlasAI Agent: Chave GEMINI_API_KEY validada com sucesso no backend.")
    except ValueError as exc:
        logger.warning("AtlasAI Agent aviso de inicialização: %s", exc)

    # Garante que o diretório de uploads existe
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="AtlasAI API", lifespan=lifespan)

# Monta diretório de mídias para visualização segura no frontend
upload_path = Path(settings.upload_dir)
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(upload_path)), name="media")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ad_accounts.router)
app.include_router(campaigns.router)
app.include_router(optimization_rules.router)
app.include_router(creatives.router)
app.include_router(agent_actions.router)
app.include_router(conversations.router)
app.include_router(instagram.router)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
