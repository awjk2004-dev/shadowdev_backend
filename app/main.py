"""
نقطة الدخول لتطبيق ShadowDev API
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 بدء {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"🌐 http://localhost:8000")
    print(f"📚 http://localhost:8000/docs")
    yield
    print("🛑 إغلاق الخادم...")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="نظام النهوض — Backend API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "alive",
        "message": "🚀 ShadowDev API يعمل",
    }


@app.get("/health", tags=["Root"])
async def health():
    from sqlalchemy import text
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return {"api": "healthy", "database": db_status}
