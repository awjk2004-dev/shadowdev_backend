from datetime import datetime
from decimal import Decimal
from sqlalchemy import Integer, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class WeightEntry(Base):
    __tablename__ = "weight_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0)
    
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<WeightEntry(user_id={self.user_id}, weight={self.weight})>"