"""
اتصال MySQL غير المتزامن + Session Management
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# ===== محرك الاتصال غير المتزامن =====
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,        # طباعة SQL في وضع التطوير
    pool_pre_ping=True,          # يتحقق من الاتصال قبل كل استعلام
    pool_recycle=3600,           # يعيد الاتصال كل ساعة (MySQL timeout)
    pool_size=5,                 # 5 اتصالات جاهزة
    max_overflow=10,             # يسمح بـ 10 إضافية عند الحاجة
)


# ===== صانع الجلسات =====
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,      # مهم: يمنع مشاكل async
    autoflush=False,
)


# ===== قاعدة كل الموديلات =====
class Base(DeclarativeBase):
    """الأب لكل جداولنا"""
    pass


# ===== Dependency للـ FastAPI =====
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    يوفر Session لكل طلب، ويضمن إغلاقه بعد الانتهاء.
    يُستخدم في endpoints هكذا:
        @router.get("/")
        async def route(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()