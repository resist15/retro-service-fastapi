from functools import lru_cache

from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool = False
    CORS_ORIGINS: list[AnyHttpUrl | str] = []

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    ALLOWED_HOSTS: list[str] = ["*"]

    # Database configs
    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int
    DATABASE_MAX_OVERFLOW: int

    # Redis Configs
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str

    SECRET_KEY: str
    ACCESS_TOKEN_EXP_MINS: int
    REFRESH_TOKEN_EXP_DAYS: int
    ALGORITHM: str
    LOG_LEVEL: str
    LOG_FORMAT: str
    SQLALCHEMY_LOG: bool
    ENVIRONMENT: str
    OTLP_ENDPOINT: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    FRONTEND_URL: str

    MUSIC_DIR: str

@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    return settings


settings = get_settings()
