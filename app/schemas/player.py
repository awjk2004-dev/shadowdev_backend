from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional

class PlayerResponse(BaseModel):
    xp: int
    level: int
    rank: str
    start_weight: Decimal
    target_weight: Decimal
    current_weight: Decimal
    height: Optional[Decimal] # 👈 أضفنا هذا
    updated_at: datetime

    class Config:
        from_attributes = True