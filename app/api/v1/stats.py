from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.stats import AllTimeStatsResponse, WeeklyStatsResponse
from app.services import stats_service

router = APIRouter()

@router.get("", response_model=AllTimeStatsResponse)
async def get_all_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """جلب عدد المهام المكتملة لكل بُعد (الإجمالي الكامل)"""
    return await stats_service.get_all_time_stats(db, current_user.id)


@router.get("/weekly", response_model=WeeklyStatsResponse)
async def get_weekly_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """جلب إحصائيات إنجاز المهام لآخر 7 أيام"""
    return await stats_service.get_weekly_stats(db, current_user.id)