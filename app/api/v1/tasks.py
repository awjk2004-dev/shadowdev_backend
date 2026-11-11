from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from datetime import date

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.task import Task
from app.models.task_log import TaskLog
from app.schemas.task import TaskResponse, TaskCompleteResponse, TaskCreate, TaskUpdate
from app.services import task_service

router = APIRouter()

@router.get("", response_model=List[TaskResponse])
async def get_my_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """جلب كل مهام المستخدم الحالي مع حالة الإكمال لهذا اليوم"""
    result = await db.execute(select(Task).where(Task.user_id == current_user.id, Task.is_active == True))
    tasks = result.scalars().all()

    log_result = await db.execute(
        select(TaskLog.task_id).where(
            TaskLog.user_id == current_user.id,
            TaskLog.completed_date == date.today()
        )
    )
    completed_ids = set(log_result.scalars().all())

    responses = []
    for task in tasks:
        response = TaskResponse.model_validate(task)
        response.is_completed = task.id in completed_ids
        responses.append(response)
    return responses

@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """إضافة مهمة جديدة"""
    new_task = Task(
        user_id=current_user.id,
        title=task_in.title,
        dimension=task_in.dimension,
        repeat_type=task_in.repeat_type,
        difficulty=task_in.difficulty,
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """تعديل مهمة موجودة"""
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    
    if task_in.title: task.title = task_in.title
    if task_in.dimension: task.dimension = task_in.dimension
    if task_in.repeat_type: task.repeat_type = task_in.repeat_type
    if task_in.difficulty is not None: task.difficulty = task_in.difficulty
    
    await db.commit()
    await db.refresh(task)
    return task

@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """حذف مهمة"""
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    
    await db.delete(task)
    await db.commit()
    return None

@router.post("/{task_id}/complete", response_model=TaskCompleteResponse)
async def complete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """إكمال مهمة وإضافة XP"""
    return await task_service.complete_task(db, task_id, current_user.id)