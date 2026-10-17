from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # ربط مع جدول users (1:1)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    
    # إحصائيات اللعبة
    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    rank: Mapped[str] = mapped_column(String(1), default="E")
    
    # إحصائيات الوزن
    start_weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=43.00)
    target_weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=50.00)
    current_weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=43.00)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقة بايثون (للوصول لبيانات المستخدم بسهولة)
    user: Mapped["User"] = relationship(back_populates="player")

    def __repr__(self) -> str:
        return f"<Player(user_id={self.user_id}, level={self.level}, rank='{self.rank}')>"