import secrets
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AutoDesk Kiwi API"
    app_version: str = "1.1.0"
    debug: bool = False  # SECURITY: Default to False in production

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

    # JWT Authentication settings
    jwt_secret_key: str = secrets.token_urlsafe(32)  # Auto-generate if not set
    jwt_expire_minutes: int = 1440  # 24 hours

    # Rate limiting settings
    rate_limit_per_minute: int = 60

    # Security: Allowed calendar URL domains (for SSRF protection)
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
