"""
Application configuration.

Uses pydantic-settings to load environment variables from .env file.
All settings are validated at startup — if a required var is missing,
the app fails fast with a clear error instead of silently breaking later.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the application.

    Values are loaded from environment variables, with .env file as fallback.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Application ---
    APP_NAME: str = "College Placement Intelligence Platform"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    API_V1_PREFIX: str = "/api/v1"

    # --- Security & JWT ---
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/student_helpdesk"

    # --- External APIs ---
    GEMINI_API_KEY: str = ""


# Singleton instance — import this wherever you need config
settings = Settings()
