from __future__ import annotations

from functools import lru_cache
import os
from typing import List
from urllib.parse import urlparse

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    app_name: str = "FreshCart Africa API"
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = Field(
        default="sqlite:///./freshcart_africa.db",
        validation_alias=AliasChoices("DATABASE_URL", "POSTGRES_INTERNAL_URL", "POSTGRES_URL"),
    )
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173,"
        "https://freshcart-frontend-7ut9.onrender.com"
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if not value:
            return "sqlite:///./freshcart_africa.db"

        normalized = value.strip()
        if normalized.startswith("postgres://"):
            normalized = normalized.replace("postgres://", "postgresql+psycopg://", 1)
        elif normalized.startswith("postgresql://"):
            normalized = normalized.replace("postgresql://", "postgresql+psycopg://", 1)

        parsed = urlparse(normalized)
        if (
            os.getenv("RENDER") == "true"
            and parsed.scheme.startswith("postgresql")
            and parsed.hostname in {"127.0.0.1", "localhost"}
        ):
            raise ValueError(
                "Database configuration points to localhost. "
                "Set DATABASE_URL or POSTGRES_INTERNAL_URL to your hosted Postgres connection string."
            )

        return normalized

    @property
    def cors_origins_list(self) -> List[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
