from pydantic import BaseModel
from typing import List

class SkillResponse(BaseModel):
    id: int
    name: str
    stage: int
    description: str
    icon_name: str

    class Config:
        from_attributes = True

class UserSkillResponse(BaseModel):
    skill_id: int
    name: str
    stage: int
    status: str