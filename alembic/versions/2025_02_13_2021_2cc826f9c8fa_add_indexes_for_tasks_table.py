"""Add indexes for tasks table

Revision ID: 2cc826f9c8fa
Revises: 93e6951a72a5
Create Date: 2025-02-13 20:21:07.542118+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2cc826f9c8fa'
down_revision: Union[str, None] = '93e6951a72a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create indexes with IF NOT EXISTS
    op.execute('CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks (category)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks (due_date)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_tasks_priority_due_date ON tasks (priority, due_date)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_tasks_search_gin ON tasks USING GIN(search_vector)')


def downgrade() -> None:
    # Drop the indexes
    op.execute('DROP INDEX IF EXISTS idx_tasks_category')
    op.execute('DROP INDEX IF EXISTS idx_tasks_due_date')
    op.execute('DROP INDEX IF EXISTS idx_tasks_priority_due_date')
    op.execute('DROP INDEX IF EXISTS idx_tasks_search_gin')

