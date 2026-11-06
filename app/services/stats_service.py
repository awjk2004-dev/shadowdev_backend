from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import date, timedelta

from app.models.task import Task
from app.models.task_log import TaskLog

def _empty_stats() -> dict:
    return {
        "body": 0,
        "mind": 0,
        "work": 0,
        "self_development": 0,
        "relations": 0,
        "total_completed": 0,
    }


def _fill_stats(response: dict, stats) -> dict:
    for dimension, count in stats:
        key = "self_development" if dimension == "self" else dimension
        if key in response and key != "total_completed":
            response[key] += count
            response["total_completed"] += count
    return response


async def get_weekly_stats(db: AsyncSession, user_id: int):
    # تحديد بداية الأسبوع (آخر 7 أيام)
    today = date.today()
    week_ago = today - timedelta(days=7)

    # جلب المهام المكتملة في آخر 7 أيام
    result = await db.execute(
        select(Task.dimension, func.count(TaskLog.id))
        .join(TaskLog, Task.id == TaskLog.task_id)
        .where(TaskLog.user_id == user_id, TaskLog.completed_date >= week_ago)
        .group_by(Task.dimension)
    )

    return _fill_stats(_empty_stats(), result.all())


async def get_all_time_stats(db: AsyncSession, user_id: int):
    """عدد المهام المكتملة لكل بُعد منذ بداية استخدام التطبيق"""
    result = await db.execute(
        select(Task.dimension, func.count(TaskLog.id))
        .join(TaskLog, Task.id == TaskLog.task_id)
        .where(TaskLog.user_id == user_id)
        .group_by(Task.dimension)
    )

    return _fill_stats(_empty_stats(), result.all())