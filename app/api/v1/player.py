from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from decimal import Decimal
from datetime import date
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.player import Player, sync_player_progress
from app.models.streak import Streak 
from app.models.task import Task
from app.models.task_log import TaskLog
from app.schemas.player import PlayerResponse

router = APIRouter()

# مخطط لإدخال الطول
class HeightUpdate(BaseModel):
    height: float


# مخطط لإدخال الوزن المستهدف
class TargetWeightUpdate(BaseModel):
    target_weight: float

@router.get("/me", response_model=PlayerResponse)
async def get_my_player(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """جلب بيانات اللاعب الحالي"""
    result = await db.execute(
        select(Player)
        .where(Player.user_id == current_user.id)
        .with_for_update()
    )
    player = result.scalars().first()
    
    if not player:
        raise HTTPException(status_code=404, detail="لم يتم العثور على بيانات اللاعب")

    previous_progress = (player.level, player.rank, player.skill_points)
    sync_player_progress(player)
    if (player.level, player.rank, player.skill_points) != previous_progress:
        await db.commit()

    return player

@router.get("/streak")
async def get_my_streak(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """جلب بيانات السلسلة اليومية (Streak)"""
    result = await db.execute(select(Streak).where(Streak.user_id == current_user.id))
    streak = result.scalars().first()
    if not streak:
        raise HTTPException(status_code=404, detail="لا يوجد سجل سلسلة")
    
    # كم مهمة نشطة لديه اليوم؟ وكم أكمل منها؟
    total_tasks_result = await db.execute(
        select(func.count(Task.id)).where(Task.user_id == current_user.id, Task.is_active == True)
    )
    tasks_total = total_tasks_result.scalar() or 0

    completed_tasks_result = await db.execute(
        select(func.count(TaskLog.id)).where(
            TaskLog.user_id == current_user.id,
            TaskLog.completed_date == date.today()
        )
    )
    tasks_completed = completed_tasks_result.scalar() or 0

    return {
        "current_streak": streak.current_streak,
        "best_streak": streak.best_streak,
        "freeze_count": streak.freeze_count,
        "tasks_completed": tasks_completed,
        "tasks_total": tasks_total
    }

@router.put("/height")
async def update_height(
    data: HeightUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """تحديث طول المستخدم"""
    result = await db.execute(select(Player).where(Player.user_id == current_user.id))
    player = result.scalars().first()
    if not player:
        raise HTTPException(status_code=404, detail="اللاعب غير موجود")
        
    player.height = Decimal(str(data.height))
    await db.commit()
    return {"message": "تم تحديث الطول بنجاح", "height": float(player.height)}


@router.put("/target")
@router.put("/target-weight", include_in_schema=False)
async def update_target_weight(
    data: TargetWeightUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """تحديث الوزن المستهدف للمستخدم"""
    if data.target_weight <= 0:
        raise HTTPException(status_code=400, detail="الوزن المستهدف غير صحيح")

    result = await db.execute(select(Player).where(Player.user_id == current_user.id))
    player = result.scalars().first()
    if not player:
        raise HTTPException(status_code=404, detail="اللاعب غير موجود")

    player.target_weight = Decimal(str(data.target_weight))
    await db.commit()
    return {
        "message": "تم تحديث الوزن المستهدف بنجاح",
        "target_weight": float(player.target_weight)
    }

@router.get("/bmi")
async def get_bmi(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """حساب مؤشر كتلة الجسم (BMI) وتصنيفه"""
    result = await db.execute(select(Player).where(Player.user_id == current_user.id))
    player = result.scalars().first()
    
    if not player or not player.height:
        return {"message": "الرجاء إدخال الطول أولاً لحساب مؤشر كتلة الجسم"}

    # حساب الـ BMI (الطول مخزّن بالسنتيمتر، نحوله إلى متر)
    height_m = float(player.height) / 100
    weight = float(player.current_weight)
    
    if height_m <= 0:
        return {"message": "الطول المدخل غير صحيح"}

    bmi = weight / (height_m * height_m)
    
    # التصنيف
    if bmi < 18.5:
        category = "نحيف"
        advice = "أنت بحاجة إلى زيادة وزنك، ركز على التغذية والتمارين."
    elif bmi < 25:
        category = "وزن طبيعي"
        advice = "ممتاز! حافظ على وزنك ونمط حياتك الصحي."
    elif bmi < 30:
        category = "زيادة في الوزن"
        advice = "انتبه لوزنك، قد تحتاج لتقليل السعرات وزيادة النشاط."
    else:
        category = "سمنة"
        advice = "صحتك أولاً، ننصح بمراجعة طبيب وبدء برنامج رياضي."

    return {
        "weight": weight,
        "height": height_m,
        "bmi": round(bmi, 1),
        "category": category,
        "advice": advice
    }