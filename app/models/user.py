from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Boolean, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    # ===== الحقول (Columns) =====
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(120), unique=True, index=True, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(5), default="ar")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # ===== العلاقات (Relationships) =====
    player: Mapped[Optional["Player"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    streak: Mapped[Optional["Streak"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    streak_logs: Mapped[list["StreakLog"]] = relationship(cascade="all, delete-orphan")
    tasks: Mapped[list["Task"]] = relationship(cascade="all, delete-orphan")
    task_logs: Mapped[list["TaskLog"]] = relationship(cascade="all, delete-orphan")
    user_skills: Mapped[list["UserSkill"]] = relationship(cascade="all, delete-orphan")
    weight_entries: Mapped[list["WeightEntry"]] = relationship(cascade="all, delete-orphan")
    # ===== دالة الطباعة =====
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"