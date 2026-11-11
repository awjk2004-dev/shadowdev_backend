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
    """إعادة حساب المستوى والرتبة ومنح SP عند بلوغ مستوى جديد."""
    new_level = calculate_level(player.xp)
    levels_gained = max(0, new_level - player.level)
    if levels_gained:
        player.skill_points = (player.skill_points or 10) + levels_gained
    player.level = new_level
    player.rank = calculate_rank(player.level)


def xp_to_next_level(xp: int, level: int) -> int:
    """كم XP يلزم للوصول إلى المستوى التالي (الحد التالي: 100 * level²)."""
    return max(0, 100 * (level ** 2) - xp)


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # ربط مع جدول users (1:1)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    
    # إحصائيات اللعبة
    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    rank: Mapped[str] = mapped_column(String(1), default="E")
    skill_points: Mapped[int] = mapped_column(
        Integer, default=10, server_default="10", nullable=False
    )
    
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

    @property
    def xp_to_next_level(self) -> int:
        return xp_to_next_level(self.xp, self.level)