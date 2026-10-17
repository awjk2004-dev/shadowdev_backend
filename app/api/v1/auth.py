from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services import user_service

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    تسجيل مستخدم جديد.
    يقوم بإنشاء الحساب، اللاعب، السلسلة، والمهام الافتراضية.
    """
    new_user = await user_service.register_user(db, user_in)
    return new_user