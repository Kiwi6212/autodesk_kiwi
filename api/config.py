import os
import secrets
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


def _get_or_create_jwt_secret() -> str:
    env_secret = os.getenv("JWT_SECRET_KEY")
    if env_secret and env_secret != "CHANGEZ-MOI-EN-PRODUCTION-avec-une-cle-secrete-unique":
        return env_secret

    secret_file = Path(__file__).parent / ".jwt_secret"
    if secret_file.exists():
        return secret_file.read_text().strip()

    new_secret = secrets.token_urlsafe(32)
    secret_file.write_text(new_secret)
    return new_secret


class Settings(BaseSettings):
    app_name: str = "AutoDesk Kiwi API"
    app_version: str = "1.2.0"
    debug: bool = False

    database_url: str = "sqlite:///data.db"

    cors_origins: list[str] = [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "http://localhost:8000"
    ]

    user_agent: str = "AutoDeskKiwi/1.0 (kiwi-app-local-dev)"
    api_timeout: float = 12.0

    hyperplanning_url: str = ""

    jwt_secret_key: str = _get_or_create_jwt_secret()
    jwt_expire_minutes: int = 1440

    rate_limit_per_minute: int = 60

    allowed_calendar_domains: list[str] = [
        "hyperplanning.fr",
        "ensup.eu",
        "hp-cgy.ensup.eu",
        "extranet-hp-cgy.ensup.eu"
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings():
    return Settings()
