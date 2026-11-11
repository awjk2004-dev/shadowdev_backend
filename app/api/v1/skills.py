from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.player import Player, sync_player_progress
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.schemas.skill import (
    SkillTreeResetResponse,
    SkillUnlockResponse,
    UserSkillResponse,
)

router = APIRouter()


def _skill_response(user_skill: UserSkill) -> dict:
    skill = user_skill.skill
    return {
        "skill_id": skill.id,
        "skill_key": skill.skill_key,
        "name": skill.name,
        "stage": skill.stage,
        "description": skill.description,
        "icon_name": skill.icon_name,
        "skill_type": skill.skill_type,
        "cost": skill.cost,
        "x": skill.x,
        "y": skill.y,
        "prerequisites": skill.prerequisites or [],
        "status": user_skill.status,
        "is_unlocked": user_skill.is_unlocked,
    }


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
        .join(UserSkill.skill)
        .where(
            UserSkill.user_id == current_user.id,
            Skill.skill_key.is_not(None),
        )
        .order_by(UserSkill.skill_id)
    )
    user_skills = result.scalars().all()
    return [_skill_response(user_skill) for user_skill in user_skills]


@router.post("/me/reset", response_model=SkillTreeResetResponse)
async def reset_my_skill_tree(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    player_result = await db.execute(
        select(Player).where(Player.user_id == current_user.id).with_for_update()
    )
    player = player_result.scalars().first()
    if not player:
        raise HTTPException(status_code=404, detail="بيانات اللاعب غير موجودة")

    sync_player_progress(player)
    player.skill_points = 10 + max(player.level - 1, 0)

    user_skills_result = await db.execute(
        select(UserSkill)
        .join(UserSkill.skill)
        .where(
            UserSkill.user_id == current_user.id,
            Skill.skill_key.is_not(None),
        )
        .with_for_update()
    )
    for user_skill in user_skills_result.scalars().all():
        user_skill.is_unlocked = False

    await db.commit()
    return {
        "skill_points": player.skill_points,
        "message": "تمت إعادة تعيين الشجرة واستعادة نقاط المهارات المكتسبة",
    }


@router.post(
    "/me/{skill_id}/unlock",
    response_model=SkillUnlockResponse,
)
async def unlock_skill(
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    player_result = await db.execute(
        select(Player).where(Player.user_id == current_user.id).with_for_update()
    )
    player = player_result.scalars().first()
    if not player:
        raise HTTPException(status_code=404, detail="بيانات اللاعب غير موجودة")

    user_skill_result = await db.execute(
        select(UserSkill)
        .options(joinedload(UserSkill.skill))
        .where(
            UserSkill.user_id == current_user.id,
            UserSkill.skill_id == skill_id,
        )
        .with_for_update()
    )
    user_skill = user_skill_result.scalars().first()
    if (
        not user_skill
        or user_skill.skill.skill_key is None
        or user_skill.skill.cost is None
    ):
        raise HTTPException(status_code=404, detail="المهارة غير موجودة")
    if user_skill.is_unlocked:
        raise HTTPException(status_code=409, detail="المهارة مفتوحة بالفعل")

    prerequisites = set(user_skill.skill.prerequisites or [])
    if prerequisites:
        unlocked_result = await db.execute(
            select(Skill.skill_key)
            .join(UserSkill, UserSkill.skill_id == Skill.id)
            .where(
                UserSkill.user_id == current_user.id,
                UserSkill.is_unlocked.is_(True),
                Skill.skill_key.in_(prerequisites),
            )
        )
        unlocked_keys = set(unlocked_result.scalars().all())
        missing = prerequisites - unlocked_keys
        if missing:
            raise HTTPException(
                status_code=400,
                detail="يجب فتح المهارات المطلوبة أولاً",
            )

    if player.skill_points < user_skill.skill.cost:
        raise HTTPException(status_code=400, detail="نقاط المهارات غير كافية")

    player.skill_points -= user_skill.skill.cost
    user_skill.is_unlocked = True
    await db.commit()
    await db.refresh(user_skill)

    response = _skill_response(user_skill)
    response["skill_points"] = player.skill_points
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
    return _skill_response(user_skill)