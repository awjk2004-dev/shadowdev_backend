"""Add persistent skill tree and skill points.

Revision ID: c4186ad30b21
Revises: b7e91a4c26d1
"""
import math
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4186ad30b21"
down_revision: Union[str, None] = "b7e91a4c26d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SKILL_TREE = (
    {
        "skill_key": "discipline",
        "name": "الانضباط الأساسي",
        "description": "أساس كل تقدم. الالتزام الصغير المتكرر يتغلب على الحماس المؤقت.",
        "skill_type": "passive",
        "cost": 1,
        "x": 700,
        "y": 1560,
        "stage": 1,
        "icon_name": "shield",
        "prerequisites": [],
    },
    {
        "skill_key": "focus",
        "name": "التركيز",
        "description": "زيادة القدرة على البقاء في المهمة الواحدة دون تشتت.",
        "skill_type": "passive",
        "cost": 1,
        "x": 300,
        "y": 1260,
        "stage": 1,
        "icon_name": "center_focus_strong",
        "prerequisites": ["discipline"],
    },
    {
        "skill_key": "awareness",
        "name": "الوعي",
        "description": "ملاحظة أنماطك اليومية ومعرفة ما يستهلك طاقتك.",
        "skill_type": "active",
        "cost": 1,
        "x": 700,
        "y": 1260,
        "stage": 1,
        "icon_name": "visibility",
        "prerequisites": ["discipline"],
    },
    {
        "skill_key": "endurance",
        "name": "التحمل",
        "description": "القدرة على الاستمرار عندما تخف الحماسة الأولى.",
        "skill_type": "passive",
        "cost": 1,
        "x": 1100,
        "y": 1260,
        "stage": 1,
        "icon_name": "favorite",
        "prerequisites": ["discipline"],
    },
    {
        "skill_key": "deep_work",
        "name": "العمل العميق",
        "description": "جلسات طويلة من التركيز بلا مقاطعات لبناء مخرجات حقيقية.",
        "skill_type": "passive",
        "cost": 2,
        "x": 220,
        "y": 960,
        "stage": 2,
        "icon_name": "psychology",
        "prerequisites": ["focus"],
    },
    {
        "skill_key": "mind_fortress",
        "name": "حصن العقل",
        "description": "مقاومة المشتتات والأفكار السلبية أثناء العمل.",
        "skill_type": "passive",
        "cost": 2,
        "x": 480,
        "y": 960,
        "stage": 2,
        "icon_name": "castle",
        "prerequisites": ["focus"],
    },
    {
        "skill_key": "balance",
        "name": "الاتزان",
        "description": "موازنة العمل والراحة والعلاقات دون انهيار أي جانب.",
        "skill_type": "passive",
        "cost": 2,
        "x": 700,
        "y": 960,
        "stage": 2,
        "icon_name": "balance",
        "prerequisites": ["awareness"],
    },
    {
        "skill_key": "void_step",
        "name": "خطوة الفراغ",
        "description": "التقدم السريع في المهام الصغيرة المتتالية دون توقف.",
        "skill_type": "active",
        "cost": 2,
        "x": 880,
        "y": 960,
        "stage": 2,
        "icon_name": "air",
        "prerequisites": ["endurance"],
    },
    {
        "skill_key": "agility",
        "name": "الرشاقة",
        "description": "التحرك بين المهام بذكاء والحفاظ على زخم الإنجاز.",
        "skill_type": "active",
        "cost": 2,
        "x": 1120,
        "y": 960,
        "stage": 2,
        "icon_name": "bolt",
        "prerequisites": ["endurance"],
    },
    {
        "skill_key": "iron_will",
        "name": "الإرادة الحديدية",
        "description": "تنفيذ ما قررته حتى عندما لا ترغب في ذلك.",
        "skill_type": "passive",
        "cost": 3,
        "x": 350,
        "y": 660,
        "stage": 2,
        "icon_name": "security",
        "prerequisites": ["mind_fortress"],
    },
    {
        "skill_key": "shadow_mind",
        "name": "عقل الظل",
        "description": "تحويل الضغط والتعب إلى تركيز بارد وحساب هادئ.",
        "skill_type": "passive",
        "cost": 3,
        "x": 560,
        "y": 660,
        "stage": 2,
        "icon_name": "dark_mode",
        "prerequisites": ["deep_work", "mind_fortress"],
    },
    {
        "skill_key": "phantom",
        "name": "الظل الخفي",
        "description": "إنجاز العمل بهدوء بعيداً عن الضوضاء والمقاطعات.",
        "skill_type": "active",
        "cost": 3,
        "x": 880,
        "y": 660,
        "stage": 2,
        "icon_name": "blur_on",
        "prerequisites": ["void_step"],
    },
    {
        "skill_key": "battle_focus",
        "name": "تركيز القتال",
        "description": "دخول حالة انغماس كامل عند اقتراب الموعد النهائي.",
        "skill_type": "active",
        "cost": 3,
        "x": 1120,
        "y": 660,
        "stage": 2,
        "icon_name": "sports_martial_arts",
        "prerequisites": ["void_step", "agility"],
    },
    {
        "skill_key": "shadow_master",
        "name": "سيد الظل",
        "description": "السيطرة على وقتك وطاقتك لتصبح أنت من يقود النظام.",
        "skill_type": "active",
        "cost": 5,
        "x": 700,
        "y": 360,
        "stage": 3,
        "icon_name": "auto_awesome",
        "prerequisites": ["shadow_mind", "phantom"],
    },
    {
        "skill_key": "ascended",
        "name": "الارتقاء",
        "description": "قمة الشجرة: نظام حياة متكامل يعمل حتى في أصعب الأيام.",
        "skill_type": "passive",
        "cost": 8,
        "x": 700,
        "y": 120,
        "stage": 3,
        "icon_name": "workspace_premium",
        "prerequisites": ["shadow_master", "iron_will", "battle_focus"],
    },
)


def upgrade() -> None:
    op.add_column("players", sa.Column("skill_points", sa.Integer(), nullable=False, server_default="10"))
    op.add_column("skills", sa.Column("skill_key", sa.String(length=50), nullable=True))
    op.add_column("skills", sa.Column("skill_type", sa.String(length=20), nullable=True))
    op.add_column("skills", sa.Column("cost", sa.Integer(), nullable=True))
    op.add_column("skills", sa.Column("x", sa.Float(), nullable=True))
    op.add_column("skills", sa.Column("y", sa.Float(), nullable=True))
    op.add_column("skills", sa.Column("prerequisites", sa.JSON(), nullable=True))
    op.add_column(
        "user_skills",
        sa.Column("is_unlocked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_unique_constraint("uq_skills_skill_key", "skills", ["skill_key"])

    bind = op.get_bind()
    skills = sa.table(
        "skills",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.String()),
        sa.column("stage", sa.Integer()),
        sa.column("description", sa.String()),
        sa.column("icon_name", sa.String()),
        sa.column("skill_key", sa.String()),
        sa.column("skill_type", sa.String()),
        sa.column("cost", sa.Integer()),
        sa.column("x", sa.Float()),
        sa.column("y", sa.Float()),
        sa.column("prerequisites", sa.JSON()),
    )
    user_skills = sa.table(
        "user_skills",
        sa.column("user_id", sa.Integer()),
        sa.column("skill_id", sa.Integer()),
        sa.column("status", sa.String()),
        sa.column("is_unlocked", sa.Boolean()),
    )
    users = sa.table("users", sa.column("id", sa.Integer()))

    skill_ids: list[int] = []
    for skill in SKILL_TREE:
        existing = bind.execute(
            sa.select(skills.c.id).where(
                sa.or_(
                    skills.c.skill_key == skill["skill_key"],
                    skills.c.name == skill["name"],
                )
            )
        ).first()
        values = {**skill}
        if existing:
            skill_id = existing.id
            bind.execute(
                skills.update().where(skills.c.id == skill_id).values(**values)
            )
        else:
            bind.execute(skills.insert().values(**values))
            skill_id = bind.execute(
                sa.select(skills.c.id).where(
                    skills.c.skill_key == skill["skill_key"]
                )
            ).scalar_one()
        skill_ids.append(skill_id)

    existing_users = bind.execute(sa.select(users.c.id)).scalars().all()
    for user_id in existing_users:
        for skill_id in skill_ids:
            existing = bind.execute(
                sa.select(user_skills.c.user_id).where(
                    user_skills.c.user_id == user_id,
                    user_skills.c.skill_id == skill_id,
                )
            ).first()
            if not existing:
                bind.execute(
                    user_skills.insert().values(
                        user_id=user_id,
                        skill_id=skill_id,
                        status="beginner",
                        is_unlocked=False,
                    )
                )

    players = sa.table(
        "players",
        sa.column("id", sa.Integer()),
        sa.column("xp", sa.Integer()),
        sa.column("level", sa.Integer()),
        sa.column("rank", sa.String()),
        sa.column("skill_points", sa.Integer()),
    )
    for player_id, xp in bind.execute(
        sa.select(players.c.id, players.c.xp)
    ).all():
        level = int(math.sqrt(max(xp, 0) / 100)) + 1
        rank = (
            "S"
            if level >= 50
            else "A"
            if level >= 35
            else "B"
            if level >= 20
            else "C"
            if level >= 10
            else "D"
            if level >= 5
            else "E"
        )
        bind.execute(
            players.update()
            .where(players.c.id == player_id)
            .values(level=level, rank=rank, skill_points=10 + level - 1)
        )


def downgrade() -> None:
    bind = op.get_bind()
    skills = sa.table(
        "skills",
        sa.column("id", sa.Integer()),
        sa.column("skill_key", sa.String()),
    )
    user_skills = sa.table(
        "user_skills",
        sa.column("skill_id", sa.Integer()),
    )
    tree_keys = [skill["skill_key"] for skill in SKILL_TREE]
    tree_skill_ids = sa.select(skills.c.id).where(skills.c.skill_key.in_(tree_keys))
    bind.execute(user_skills.delete().where(user_skills.c.skill_id.in_(tree_skill_ids)))
    bind.execute(skills.delete().where(skills.c.skill_key.in_(tree_keys)))

    op.drop_constraint("uq_skills_skill_key", "skills", type_="unique")
    op.drop_column("user_skills", "is_unlocked")
    op.drop_column("skills", "prerequisites")
    op.drop_column("skills", "y")
    op.drop_column("skills", "x")
    op.drop_column("skills", "cost")
    op.drop_column("skills", "skill_type")
    op.drop_column("skills", "skill_key")
    op.drop_column("players", "skill_points")
