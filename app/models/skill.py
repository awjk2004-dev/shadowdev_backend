from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    stage: Mapped[int] = mapped_column(Integer) # 1, 2, 3
    description: Mapped[str] = mapped_column(String(255))
    icon_name: Mapped[str] = mapped_column(String(50))

    # علاقة بايثون
    user_skills: Mapped[list["UserSkill"]] = relationship(back_populates="skill", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Skill(name='{self.name}', stage={self.stage})>"