from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from datetime import date

from app.models.task import Task
from app.models.task_log import TaskLog
from app.models.player import Player, sync_player_progress
from app.models.streak import Streak
from app.models.streak_log import StreakLog


async def complete_task(db: AsyncSession, task_id: int, user_id: int):
    # 1. جلب المهمة والتأكد أنها للمستخدم
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user_id))
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")

    today = date.today()

    # 2. التأكد أن المهمة لم تكتمل اليوم بالفعل (منع الغش)
    log_result = await db.execute(
        select(TaskLog).where(
            TaskLog.task_id == task_id, 
            TaskLog.completed_date == today
        )
    )
    if log_result.scalars().first():
        raise HTTPException(status_code=400, detail="لقد أكملت هذه المهمة بالفعل اليوم")

    # 3. منح XP حسب صعوبة المهمة
    xp_earned = task.xp_reward
    new_log = TaskLog(
        task_id=task.id,
        user_id=user_id,
        completed_date=today,
        xp_earned=xp_earned
    )
    db.add(new_log)

    # 4. تحديث اللاعب (+10 XP)
    player_result = await db.execute(select(Player).where(Player.user_id == user_id))
    player = player_result.scalars().first()
    
    player.xp += xp_earned
    sync_player_progress(player)

    # 5. التحقق: هل أكمل كل مهام اليوم؟ (+60 XP)
    is_day_complete = False
    
    # كم مهمة نشطة لديه؟
    total_tasks_result = await db.execute(
        select(func.count(Task.id)).where(Task.user_id == user_id, Task.is_active == True)
    )
    total_tasks = total_tasks_result.scalar()
    
    # كم مهمة أكملها اليوم؟
    completed_tasks_result = await db.execute(
        select(func.count(TaskLog.id)).where(TaskLog.user_id == user_id, TaskLog.completed_date == today)
    )
    completed_tasks = completed_tasks_result.scalar()

    if completed_tasks == total_tasks and total_tasks > 0:
        is_day_complete = True
        player.xp += 60 # مكافأة اليوم
        sync_player_progress(player)

    # 6. تحديث نظام الـ Streak (السلسلة اليومية)
    # نقفل صف السلسلة الخاص بالمستخدم حتى لا تتعارض الطلبات المتزامنة
    streak_result = await db.execute(
        select(Streak).where(Streak.user_id == user_id).with_for_update()
    )
    streak = streak_result.scalars().first()

    if not streak:
        streak = Streak(user_id=user_id)
        db.add(streak)
        await db.flush()

    # هل يوجد سجل لهذا المستخدم في تاريخ اليوم؟
    streak_log_result = await db.execute(
        select(StreakLog)
        .where(StreakLog.user_id == user_id, StreakLog.date == today)
        .with_for_update()
    )
    today_log = streak_log_result.scalars().first()

    if today_log:
        # السجل موجود مسبقاً: نحدّثه فقط دون زيادة عداد السلسلة
        today_log.status = "completed"
        today_log.tasks_completed += 1
        today_log.tasks_total = total_tasks
        today_log.xp_earned += xp_earned
    else:
        # أول مهمة تُكمل اليوم: ننشئ السجل ثم نزيد عداد السلسلة
        # نflush التغييرات السابقة أولاً حتى يقتصر الـ savepoint على سجل السلسلة
        await db.flush()
        try:
            async with db.begin_nested():
                db.add(
                    StreakLog(
                        user_id=user_id,
                        date=today,
                        status="completed",
                        tasks_completed=1,
                        tasks_total=total_tasks,
                        xp_earned=xp_earned,
                    )
                )
                await db.flush()

            streak.current_streak += 1
            if streak.current_streak > streak.best_streak:
                streak.best_streak = streak.current_streak
            streak.last_completed_date = today
        except IntegrityError:
            # طلب آخر أنشأ سجل اليوم في نفس اللحظة: نحدّث السجل الموجود
            existing_result = await db.execute(
                select(StreakLog)
                .where(StreakLog.user_id == user_id, StreakLog.date == today)
                .with_for_update()
            )
            existing_log = existing_result.scalars().first()

            if existing_log is None:
                raise

            existing_log.status = "completed"
            existing_log.tasks_completed += 1
            existing_log.tasks_total = total_tasks
            existing_log.xp_earned += xp_earned

    await db.commit()

    return {
        "message": "تم إكمال المهمة بنجاح",
        "xp_earned": xp_earned,
        "total_xp": player.xp,
        "current_level": player.level,
        "rank": player.rank,
        "is_day_complete": is_day_complete
    }