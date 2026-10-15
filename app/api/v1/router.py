"""
مجمّع كل راوترات الإصدار الأول
"""
from fastapi import APIRouter

# من الآن، هذه الراوترات فارغة — سنملأها تدريجياً
# from app.api.v1 import auth, tasks, player, skills, weight

api_router = APIRouter()


@api_router.get("/ping", tags=["Root"])
async def ping():
    """فحص سريع أن API v1 يعمل"""
    return {"pong": True, "version": "v1"}


# ===== سنضيفها لاحقاً =====
# api_router.include_router(auth.router,     prefix="/auth",     tags=["Auth"])
# api_router.include_router(player.router,   prefix="/player",   tags=["Player"])
# api_router.include_router(tasks.router,    prefix="/tasks",    tags=["Tasks"])
# api_router.include_router(skills.router,   prefix="/skills",   tags=["Skills"])
# api_router.include_router(weight.router,   prefix="/weight",   tags=["Weight"])