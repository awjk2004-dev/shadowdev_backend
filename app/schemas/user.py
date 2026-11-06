from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date, datetime

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    birth_date: Optional[date] = None

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