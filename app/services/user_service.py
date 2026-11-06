from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.models.user import User
from app.models.player import Player
from app.models.streak import Streak
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.models.task import Task
from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from app.core.security import verify_password

# ==========================================
# المهام الافتراضية الترحيبية (محايدة لأي مستخدم)
# ==========================================
DEFAULT_TASKS = [
    {"title": "قراءة 10 صفحات من كتاب", "dimension": "mind", "repeat_type": "daily"},
    {"title": "ممارسة الرياضة لمدة 15 دقيقة", "dimension": "body", "repeat_type": "daily"},
    {"title": "تحديد هدف اليوم", "dimension": "self", "repeat_type": "daily"},
]


async def register_user(db: AsyncSession, user_in: UserCreate) -> User:
    # 1. التحقق: هل اسم المستخدم موجود مسبقاً؟
    result = await db.execute(select(User).where(User.username == user_in.username))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="اسم المستخدم مسجل بالفعل"
        )

    # 2. التحقق: هل البريد الإلكتروني موجود مسبقاً؟
    if user_in.email:
        result = await db.execute(select(User).where(User.email == user_in.email))
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="البريد الإلكتروني مسجل بالفعل"
            )

    # 3. إنشاء المستخدم (مع تشفير كلمة المرور)
    new_user = User(
        username=user_in.username,
        full_name=user_in.full_name,
        email=user_in.email,
        phone=user_in.phone,
        country=user_in.country,
        birth_date=user_in.birth_date,
        hashed_password=get_password_hash(user_in.password)
    )
    db.add(new_user)
    
    # 4. (مهم) نحتاج حفظ المستخدم أولاً للحصول على الـ ID الخاص به
    await db.flush() 

    # 5. إنشاء اللاعب والسلسلة (Streak) تلقائياً مع تمرير القيم الافتراضية
    new_player = Player(
        user_id=new_user.id,
        xp=0,
        level=1,
        rank="E",
        start_weight=0,
        target_weight=0,
        current_weight=0
    )
    new_streak = Streak(
        user_id=new_user.id,
        current_streak=0,
        best_streak=0,
        freeze_count=2,
        freeze_used_this_month=0
    )
    db.add(new_player)
    db.add(new_streak)

        # 6. نسخ المهام الافتراضية للمستخدم
    for task_data in DEFAULT_TASKS:
        new_task = Task(
            user_id=new_user.id,
            title=task_data["title"],
            dimension=task_data["dimension"],
            repeat_type=task_data.get("repeat_type", "daily") # 👈 إضافة نوع التكرار
        )
        db.add(new_task)

    # 7. نسخ المهارات (من جدول skills إلى user_skills)
    # نقرأ كل المهارات الـ 12 من قاعدة البيانات
    skills_result = await db.execute(select(Skill))
    all_skills = skills_result.scalars().all()
    
    for skill in all_skills:
        new_user_skill = UserSkill(
            user_id=new_user.id,
            skill_id=skill.id,
            status="beginner"
        )
        db.add(new_user_skill)

    # 8. حفظ كل شيء في قاعدة البيانات (Commit)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    """التحقق من صحة اسم المستخدم وكلمة المرور"""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
        
    return user