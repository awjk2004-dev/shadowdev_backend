from pydantic import BaseModel, Field
from typing import List

class SkillResponse(BaseModel):
    id: int
    name: str
    stage: int
    description: str
    icon_name: str
    skill_key: str | None = None
    skill_type: str | None = None
    cost: int | None = None
    x: float | None = None
    y: float | None = None
    prerequisites: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True

class UserSkillResponse(BaseModel):
    skill_id: int
    skill_key: str | None = None
    name: str
    stage: int
    description: str | None = None
    icon_name: str | None = None
    skill_type: str | None = None
    cost: int | None = None
    x: float | None = None
    y: float | None = None
    prerequisites: list[str] = Field(default_factory=list)
    status: str
    is_unlocked: bool = False


class SkillUnlockResponse(UserSkillResponse):
    skill_points: int


class SkillTreeResetResponse(BaseModel):
    skill_points: int
    message: str