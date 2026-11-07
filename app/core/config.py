"""
إعدادات التطبيق — تُقرأ من ملف .env
"""
import logging
from functools import lru_cache
from typing import Literal
from pydantic import Field, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """كل إعدادات ShadowDev في مكان واحد"""

    # ===== App =====
    APP_NAME: str = "ShadowDev"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # ===== Database (PostgreSQL) =====
    DATABASE_URL: str = Field(..., description="رابط اتصال PostgreSQL غير المتزامن")

    # ===== Security =====
    SECRET_KEY: str = Field(..., min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 يوم
    API_RATE_LIMIT_REQUESTS: int = Field(default=120, gt=0)
    API_RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, gt=0)
    LOGIN_FAILURE_LIMIT: int = Field(default=5, gt=0)
    LOGIN_LOCKOUT_SECONDS: int = Field(default=900, gt=0)

    # ===== CORS =====
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            if self.DEBUG:
                raise ValueError("DEBUG must be disabled in production")
            if self.SECRET_KEY.lower() in {
                "your_secret_key_here",
                "changeme",
                "change-me",
            }:
                raise ValueError("SECRET_KEY must be replaced in production")
            if any(
                origin == "*" or not origin.startswith("https://")
                for origin in self.CORS_ORIGINS
            ):
                raise ValueError(
                    "Production CORS_ORIGINS must contain only explicit HTTPS origins"
                )
        return self

    # ===== Database URL =====
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """إزالة أي إضافات قديمة خاصة بـ MySQL والتأكد من استخدام psycopg."""
        if not isinstance(value, str):
            return value

        value = value.strip()

        if not value:
            logger.warning(
                "DATABASE_URL is empty or not found in .env — database connection will fail."
            )
            return value

        value = value.replace("?charset=utf8mb4", "")

        if value.startswith("postgres://"):
            value = "postgresql+psycopg://" + value[len("postgres://"):]
        elif value.startswith("postgresql://"):
            value = "postgresql+psycopg://" + value[len("postgresql://"):]
        elif value.startswith("postgresql+asyncpg://"):
            value = "postgresql+psycopg://" + value[len("postgresql+asyncpg://"):]

        return value

    # ===== Pydantic Settings Config =====
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    إرجاع نسخة واحدة من الإعدادات (Singleton)
    lru_cache يضمن أننا نقرأ .env مرة واحدة فقط
    """
    try:
        return Settings()
    except ValidationError as exc:
        missing = [
            error["loc"][0]
            for error in exc.errors()
            if error.get("type") == "missing"
        ]
        if "DATABASE_URL" in missing:
            logger.warning(
                "DATABASE_URL is not found in .env — database connection will fail."
            )
        raise
# نسخة جاهزة للاستخدام في كل المشروع
settings = get_settings()