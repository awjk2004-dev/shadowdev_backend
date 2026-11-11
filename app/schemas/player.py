from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional

class PlayerResponse(BaseModel):
    xp: int
    level: int
    rank: str
    xp_to_next_level: int # كم XP يلزم للوصول للمستوى التالي
    skill_points: int
    start_weight: Decimal
    target_weight: Decimal
    current_weight: Decimal
    height: Optional[Decimal] # 👈 أضفنا هذا
    updated_at: datetime

    class Config:
        from_attributes = True