from pydantic import BaseModel, EmailStr, Field
from pydantic import field_validator
from typing import Optional
from datetime import date, datetime


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=12, max_length=72)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    birth_date: Optional[date] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        if len(password.encode("utf-8")) > 72:
            raise ValueError("كلمة المرور يجب ألا تتجاوز 72 بايت")
        if not any(char.islower() for char in password):
            raise ValueError("كلمة المرور يجب أن تحتوي على حرف صغير")
        if not any(char.isupper() for char in password):
            raise ValueError("كلمة المرور يجب أن تحتوي على حرف كبير")
        if not any(char.isdigit() for char in password):
            raise ValueError("كلمة المرور يجب أن تحتوي على رقم")
        if not any(not char.isalnum() for char in password):
            raise ValueError("كلمة المرور يجب أن تحتوي على رمز")

        normalized = "".join(
            char for char in password.casefold() if char.isalnum()
        )
        if normalized in {
            "password123",
            "password1234",
            "qwerty12345",
            "letmein12345",
            "welcome12345",
            "admin123456",
        }:
            raise ValueError("كلمة المرور شائعة جداً")
        return password


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    country: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str