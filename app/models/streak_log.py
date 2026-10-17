from datetime import datetime, date
from typing import Optional
from sqlalchemy import Integer, Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

class StreakLog(Base):
    __tablename__ = "streak_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    # تاريخ اليوم
    date: Mapped[date] = mapped_column(Date, index=True)
    
    # حالة اليوم: مكتمل (completed)، مجمد (frozen)، منكسر (broken)
    status: Mapped[str] = mapped_column(String(20)) 
    
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    tasks_total: Mapped[int] = mapped_column(Integer, default=0)
    
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # قاعدة صارمة: لا يمكن تسجيل نفس اليوم مرتين لنفس المستخدم
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_user_streak_date"),
    )

    def __repr__(self) -> str:
        return f"<StreakLog(user_id={self.user_id}, date={self.date}, status='{self.status}')>"