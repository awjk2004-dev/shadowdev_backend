from sqlalchemy import Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    stage: Mapped[int] = mapped_column(Integer) # 1, 2, 3
    description: Mapped[str] = mapped_column(String(255))
    icon_name: Mapped[str] = mapped_column(String(50))
    skill_key: Mapped[str | None] = mapped_column(String(50), unique=True)
    skill_type: Mapped[str | None] = mapped_column(String(20))
    cost: Mapped[int | None] = mapped_column(Integer)
    x: Mapped[float | None] = mapped_column(Float)
    y: Mapped[float | None] = mapped_column(Float)
    prerequisites: Mapped[list[str] | None] = mapped_column(JSON)

    # علاقة بايثون
    user_skills: Mapped[list["UserSkill"]] = relationship(back_populates="skill", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Skill(name='{self.name}', stage={self.stage})>"