"""Add task difficulty and reward levels.

Revision ID: b7e91a4c26d1
Revises: a32a4bb8dbcc
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7e91a4c26d1"
down_revision: Union[str, None] = "a32a4bb8dbcc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column(
            "difficulty",
            sa.String(length=10),
            server_default="easy",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("tasks", "difficulty")
