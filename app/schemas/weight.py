from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

class WeightEntryCreate(BaseModel):
    weight: Decimal

class WeightEntryResponse(BaseModel):
    id: int
    weight: Decimal
    xp_awarded: int
    recorded_at: datetime

    class Config:
        from_attributes = True