from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

# هذا يخبر Swagger بمكان زر تسجيل الدخول
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    هذه الدالة تعمل كحرس:
    1. تقرأ التوكن من الطلب.
    2. تفك تشفيره للتأكد أنه صادر من سيرفرنا.
    3. تجلب المستخدم من قاعدة البيانات.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="التوكن غير صالح أو منتهي الصلاحية",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # فك تشفير التوكن
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # جلب المستخدم من قاعدة البيانات
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="الحساب غير نشط")
        
    return user