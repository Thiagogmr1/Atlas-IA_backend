from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str
    db_password: str
    db_name: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    account_deletion_grace_days: int = 30

    gemini_api_key: str
    gemini_model: str
    gemini_thinking_level: str | None = None  # opcional: low, medium ou high
    chat_history_limit: int = 40

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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


settings = Settings()