from fastapi import APIRouter
from app.api.v1 import auth  # استيراد الملف الجديد

api_router = APIRouter()

@api_router.get("/ping", tags=["Root"])
async def ping():
    return {"pong": True, "version": "v1"}

# تفعيل مسارات المصادقة
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])