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
    echo=settings.DEBUG,
    pool_pre_ping=False,  # 👈 التعديل هنا: جعلناها False لتجنب خطأ aiomysql
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10,
)


# ===== صانع الجلسات =====
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,     # مهم: يمنع مشاكل async بعد الـ commit
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
            # نعطي الجلسة للـ Route
            yield session
            
            # إذا انتهى الـ Route بنجاح، نحفظ التغييرات
            await session.commit()
            
        except Exception as e:
            # إذا حدث أي خطأ (مثل رفض قاعدة البيانات لبيانات)،
            # نلغي كل التغييرات المعلقة وننظف الجلسة
            await session.rollback()
            raise e  # نرفع الخطأ ليظهر في التيرمنال (مهم جداً لمعرفة السبب)
            
        finally:
            # دائماً نغلق الجلسة في النهاية
            await session.close()