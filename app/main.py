"""
نقطة الدخول لتطبيق ShadowDev API
"""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import engine
from app.core.rate_limit import APIRateLimitMiddleware, SecurityHeadersMiddleware
from app.api.v1.router import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 بدء {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"🌐 http://localhost:8000")
    if settings.ENVIRONMENT != "production":
        print(f"📚 http://localhost:8000/docs")
    yield
    print("🛑 إغلاق الخادم...")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="نظام النهوض — Backend API",
    lifespan=lifespan,
    docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
    redoc_url=None if settings.ENVIRONMENT == "production" else "/redoc",
    openapi_url=None if settings.ENVIRONMENT == "production" else "/openapi.json",
)

app.add_middleware(
    APIRateLimitMiddleware,
    requests=settings.API_RATE_LIMIT_REQUESTS,
    window_seconds=settings.API_RATE_LIMIT_WINDOW_SECONDS,
)
app.add_middleware(
    SecurityHeadersMiddleware,
    production=settings.ENVIRONMENT == "production",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
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
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except SQLAlchemyError as exc:
        logger.error("Database health check failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=503, detail="قاعدة البيانات غير متاحة"
        ) from exc
    return {"api": "healthy", "database": db_status}
