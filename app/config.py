"""Cau hinh ung dung tai tu bien moi truong."""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Cau hinh trung tam cho he thong Gen-DBA."""
    ORACLE_USER: str = "gendba"
    ORACLE_PASSWORD: str = "gendba123"
    ORACLE_DSN: str = "localhost:1521/orclpdb"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    APP_ENV: str = "development"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "info"

    # Cau hinh file .env
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
