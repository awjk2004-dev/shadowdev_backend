from pydantic import BaseModel
from datetime import datetime, date
from typing import Literal, Optional

TaskDimension = Literal["mind", "body", "work", "self", "relations"]
TaskDifficulty = Literal["easy", "medium", "hard"]

class TaskCreate(BaseModel):
    title: str
    dimension: TaskDimension
    repeat_type: str = "daily"
    difficulty: TaskDifficulty = "easy"

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    dimension: Optional[TaskDimension] = None
    repeat_type: Optional[str] = None
    difficulty: Optional[TaskDifficulty] = None
    
class TaskResponse(BaseModel):
    id: int
    title: str
    dimension: str
    difficulty: TaskDifficulty
    xp_reward: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TaskLogResponse(BaseModel):
    id: int
    task_id: int
    completed_date: date
    xp_earned: int
    
    class Config:
        from_attributes = True

class TaskCompleteResponse(BaseModel):
    message: str
    xp_earned: int
    total_xp: int
    current_level: int
    rank: str
    is_day_complete: bool # هل أكمل كل مهام اليوم؟