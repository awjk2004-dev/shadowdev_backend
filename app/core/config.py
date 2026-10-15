"""
إعدادات التطبيق — تُقرأ من ملف .env
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """كل إعدادات ShadowDev في مكان واحد"""

    # ===== App =====
    APP_NAME: str = "ShadowDev"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # ===== Database =====
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "shadowdev"

    # ===== Security =====
    SECRET_KEY: str = "change_me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 يوم

    # ===== CORS =====
    CORS_ORIGINS: list[str] = ["*"]  # للتطوير فقط

    # ===== Database URL (محسوبة تلقائياً) =====
    @property
    def DATABASE_URL(self) -> str:
        """رابط اتصال MySQL غير المتزامن"""
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

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
    return Settings()


# نسخة جاهزة للاستخدام في كل المشروع
settings = get_settings()