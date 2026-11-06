"""Reset legacy default player weights to zero

Revision ID: 9b1f4c2d7e10
Revises: 2cf799a06bad
Create Date: 2026-11-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '9b1f4c2d7e10'
down_revision: Union[str, None] = '2cf799a06bad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # إعادة ضبط اللاعبين القدامى الذين ما زالوا يحملون القيم الافتراضية
    # (43 / 50) ولم يسجلوا أي وزن فعلي بعد.
    op.execute(
        """
        UPDATE players
        SET current_weight = 0,
            target_weight = 0,
            start_weight = 0
        WHERE current_weight = 43
          AND target_weight = 50
          AND start_weight = 43
          AND NOT EXISTS (
              SELECT 1 FROM weight_entries
              WHERE weight_entries.user_id = players.user_id
          )
        """
    )


def downgrade() -> None:
    pass
