from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Centralized application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AI Meeting Minutes"
    app_env: str = "development"
    debug: bool = False

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    database_host: str = "localhost"
    database_port: int = 3306
    database_name: str = "meeting_minutes"
    database_user: str = "meeting_user"
    database_password: str = "meeting_password"

    redis_url: str = "redis://localhost:6379/0"

    # A real value must be supplied by the deployment environment.  Keeping the
    # default empty avoids embedding a usable secret in application source.
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    @property
    def database_url(self) -> str:
        user = quote_plus(self.database_user)
        password = quote_plus(self.database_password)
        database = quote_plus(self.database_name)
        return f"mysql+pymysql://{user}:{password}@{self.database_host}:{self.database_port}/{database}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
