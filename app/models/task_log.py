from datetime import datetime, date
from sqlalchemy import Integer, Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class TaskLog(Base):
    __tablename__ = "task_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    # تاريخ الإكمال (بدون وقت، لأننا نمنع التكرار في نفس اليوم)
    completed_date: Mapped[date] = mapped_column(Date, index=True)
    
    xp_earned: Mapped[int] = mapped_column(Integer, default=10)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # علاقة بايثون
    task: Mapped["Task"] = relationship(back_populates="logs")

    # قاعدة صارمة: لا يمكن إكمال نفس المهمة مرتين في نفس اليوم
    __table_args__ = (
        UniqueConstraint("task_id", "completed_date", name="uq_task_completed_date"),
    )

    def __repr__(self) -> str:
        return f"<TaskLog(task_id={self.task_id}, date={self.completed_date})>"