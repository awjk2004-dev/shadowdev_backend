from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from pydantic import BaseModel  # 👈 استيراد BaseModel

from app.api.deps import get_current_user
from app.models.user import User
from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.user import UserCreate, UserResponse, Token
from app.services import user_service

router = APIRouter()

# 👇 مخطط لتحديث بيانات المستخدم
class UserUpdate(BaseModel):
    full_name: str

# 1. جلب بيانات المستخدم
@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user)
):
    """جلب بيانات المستخدم الحالي."""
    return current_user

# 2. تحديث بيانات المستخدم (الاسم فقط حالياً)
@router.put("/me", response_model=UserResponse)
async def update_user(
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """تحديث بيانات المستخدم (الاسم فقط حالياً)"""
    current_user.full_name = user_in.full_name
    await db.commit()
    await db.refresh(current_user)
    return current_user

# 3. تسجيل مستخدم جديد
@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """تسجيل مستخدم جديد."""
    new_user = await user_service.register_user(db, user_in)
    return new_user

# 4. تسجيل الدخول
@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    تسجيل الدخول.
    يعيد التوكن (Access Token) لاستخدامه في الطلبات القادمة.
    """
    user = await user_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="اسم المستخدم أو كلمة المرور غير صحيحة",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # إنشاء التوكن
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}