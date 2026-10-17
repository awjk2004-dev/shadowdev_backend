from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# 1. إعداد أداة التشفير (نستخدم bcrypt لأنها الأقوى)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. دالة تشفير كلمة المرور
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# 3. دالة التحقق (هل كلمة المرور تطابق البصمة؟)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 4. دالة إنشاء السوار (Access Token)
def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # محتوى السوار (subject هو عادةً user_id)
    to_encode = {"exp": expire, "sub": str(subject)}
    
    # تشفير السوار باستخدام SECRET_KEY (من ملف .env)
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt