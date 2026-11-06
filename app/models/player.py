from __future__ import annotations

import math
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def calculate_level(xp: int) -> int:
    """مستوى تصاعدي تربيعي: المستوى 2 عند 100 XP، 3 عند 400 XP، 4 عند 900 XP..."""
    return int(math.sqrt(max(xp, 0) / 100)) + 1


def calculate_rank(level: int) -> str:
    if level >= 50:
        return "S"
    if level >= 35:
        return "A"
    if level >= 20:
        return "B"
    if level >= 10:
        return "C"
    if level >= 5:
        return "D"
    return "E"


def sync_player_progress(player: Player) -> None:
    """إعادة حساب المستوى والرتبة من إجمالي XP."""
    player.level = calculate_level(player.xp)
    player.rank = calculate_rank(player.level)


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # ربط مع جدول users (1:1)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    
    # إحصائيات اللعبة
    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    rank: Mapped[str] = mapped_column(String(1), default="E")
    
    # إحصائيات الوزن والطول
    start_weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    target_weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    current_weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    height: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True) # الطول بالمتر
    
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # علاقة بايثون (للوصول لبيانات المستخدم بسهولة)
    user: Mapped["User"] = relationship(back_populates="player")

    def __repr__(self) -> str:
        return f"<Player(user_id={self.user_id}, level={self.level}, rank='{self.rank}')>"