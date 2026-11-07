import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.models.user import User
from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.core.rate_limit import (
    clear_login_failures,
    login_lockout_retry_after,
    record_login_failure,
)
from app.schemas.user import UserCreate, UserResponse, Token
from app.services import user_service

router = APIRouter()
logger = logging.getLogger(__name__)


class UserUpdate(BaseModel):
    full_name: str


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """جلب بيانات المستخدم الحالي."""
    return current_user

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

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """تسجيل مستخدم جديد."""
    new_user = await user_service.register_user(db, user_in)
    return new_user

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    تسجيل الدخول.
    يعيد التوكن (Access Token) لاستخدامه في الطلبات القادمة.
    """
    client_ip = request.client.host if request.client else "unknown"
    retry_after = login_lockout_retry_after(
        client_ip,
        form_data.username,
        settings.LOGIN_FAILURE_LIMIT,
        settings.LOGIN_LOCKOUT_SECONDS,
    )
    if retry_after is not None:
        logger.warning(
            "Login temporarily blocked for username=%r from client_ip=%s",
            form_data.username[:100],
            client_ip,
        )
        raise HTTPException(
            status_code=429,
            detail="محاولات دخول كثيرة، حاول مرة أخرى لاحقاً",
            headers={"Retry-After": str(retry_after)},
        )

    user = await user_service.authenticate_user(
        db, form_data.username, form_data.password
    )
    if not user:
        retry_after = record_login_failure(
            client_ip,
            form_data.username,
            settings.LOGIN_FAILURE_LIMIT,
            settings.LOGIN_LOCKOUT_SECONDS,
        )
        logger.warning(
            "Failed login for username=%r from client_ip=%s",
            form_data.username[:100],
            client_ip,
        )
        if retry_after is not None:
            raise HTTPException(
                status_code=429,
                detail="محاولات دخول كثيرة، حاول مرة أخرى لاحقاً",
                headers={"Retry-After": str(retry_after)},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="اسم المستخدم أو كلمة المرور غير صحيحة",
            headers={"WWW-Authenticate": "Bearer"},
        )

    clear_login_failures(client_ip, form_data.username)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}