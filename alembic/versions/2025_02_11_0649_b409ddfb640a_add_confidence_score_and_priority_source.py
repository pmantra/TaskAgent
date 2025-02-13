"""add_confidence_score_and_priority_source

Revision ID: b409ddfb640a
Revises: e8cf84e323bb
Create Date: 2025-02-11 06:49:29.937972+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b409ddfb640a'
down_revision: Union[str, None] = 'e8cf84e323bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

"""add_confidence_score_and_priority_source

Revision ID: add_confidence_columns
Revises: your_previous_revision
Create Date: 2025-02-06
"""
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # Add confidence_score column with a default value of 50
    op.add_column('tasks',
                  sa.Column('confidence_score', sa.Integer(),
                            nullable=False, server_default='50')
                  )

    # Add priority_source column with default 'ai'
    op.add_column('tasks',
                  sa.Column('priority_source', sa.String(),
                            nullable=False, server_default='ai')
                  )

    # Add constraint to ensure confidence_score is between 0 and 100
    op.create_check_constraint(
        'tasks_confidence_score_range',
        'tasks',
        'confidence_score >= 0 AND confidence_score <= 100'
    )

    # Add constraint to ensure priority_source is either 'ai' or 'regex'
    op.create_check_constraint(
        'tasks_priority_source_values',
        'tasks',
        "priority_source IN ('ai', 'regex')"
    )


def downgrade() -> None:
    # Remove constraints first
    op.drop_constraint('tasks_confidence_score_range', 'tasks')
    op.drop_constraint('tasks_priority_source_values', 'tasks')

    # Then remove columns
    op.drop_column('tasks', 'confidence_score')
    op.drop_column('tasks', 'priority_source')
