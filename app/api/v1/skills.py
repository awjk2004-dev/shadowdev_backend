from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.schemas.skill import UserSkillResponse

router = APIRouter()

@router.get("/me", response_model=List[UserSkillResponse])
async def get_my_skills(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """جلب مهارات المستخدم مع حالتها"""
    # نستخدم joinedload لجلب اسم المهارة في نفس الاستعلام
    result = await db.execute(
        select(UserSkill)
        .options(joinedload(UserSkill.skill))
        .where(UserSkill.user_id == current_user.id)
        .order_by(UserSkill.skill_id)
    )
    user_skills = result.scalars().all()
    
    # تحويل البيانات للشكل المطلوب
    response = []
    for us in user_skills:
        response.append({
            "skill_id": us.skill_id,
            "name": us.skill.name,
            "stage": us.skill.stage,
            "status": us.status
        })
    return response

@router.patch("/me/{skill_id}", response_model=UserSkillResponse)
async def upgrade_skill(
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ترقية مهارة (مبتدئ -> ممارس -> محارب)"""
    result = await db.execute(
        select(UserSkill)
        .options(joinedload(UserSkill.skill))
        .where(UserSkill.user_id == current_user.id, UserSkill.skill_id == skill_id)
    )
    user_skill = result.scalars().first()
    
    if not user_skill:
        raise HTTPException(status_code=404, detail="المهارة غير موجودة")
        
    if user_skill.status == "beginner":
        user_skill.status = "practitioner"
    elif user_skill.status == "practitioner":
        user_skill.status = "warrior"
    else:
        raise HTTPException(status_code=400, detail="المهارة وصلت لأقصى مستوى (محارب)")
        
    await db.commit()
    await db.refresh(user_skill)
    
    return {
        "skill_id": user_skill.skill_id,
        "name": user_skill.skill.name,
        "stage": user_skill.skill.stage,
        "status": user_skill.status
    }