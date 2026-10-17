from datetime import datetime, date
from typing import Optional
from sqlalchemy import Integer, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class Streak(Base):
    __tablename__ = "streaks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # ربط مع المستخدم (1:1)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    
    # آخر يوم أكمل فيه المستخدم مهامه
    last_completed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # نظام التجميد (Freeze)
    freeze_count: Mapped[int] = mapped_column(Integer, default=2) # تجميدتان مجانيتان شهرياً
    freeze_used_this_month: Mapped[int] = mapped_column(Integer, default=0)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقة بايثون
    user: Mapped["User"] = relationship(back_populates="streak")

    def __repr__(self) -> str:
        return f"<Streak(user_id={self.user_id}, current={self.current_streak})>"