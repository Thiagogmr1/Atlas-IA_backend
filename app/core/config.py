import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "atlas_db"

    jwt_secret: str = "dev-insecure-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    account_deletion_grace_days: int = 30

    # Configuração da IA (Gemini API)
    # A chave é estritamente confidencial e gerenciada apenas pelo backend.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_thinking_level: str | None = None  # opcional: low, medium ou high
    imagen_model: str = "imagen-3.0-generate-002"
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 50
    chat_history_limit: int = 40

    # Configuração Meta / Instagram Graph API
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_api_version: str = "v21.0"
    instagram_redirect_uri: str = "http://localhost:8000/api/integrations/instagram/callback"
    token_encryption_key: str = "default_32_byte_secret_key_for_dev_only!"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )

    def validate_gemini_config(self) -> None:
        """Valida se a chave do Gemini está devidamente configurada.
        
        Não imprime o valor da chave em logs ou exceções.
        """
        if not self.gemini_api_key or self.gemini_api_key.strip() in (
            "",
            "sua_chave_gemini_aqui",
            "fake_key",
        ):
            raise ValueError(
                "A chave GEMINI_API_KEY não foi configurada. "
                "Defina a variável no ambiente ou no arquivo .env."
            )


settings = Settings()
