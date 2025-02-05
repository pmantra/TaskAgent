"""add_search_indexes

Revision ID: 5b1818401bfa
Revises: 7c51744c2f23
Create Date: 2025-02-05 06:04:47.066389+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5b1818401bfa'
down_revision: Union[str, None] = '7c51744c2f23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Index for date searches
    op.create_index('idx_tasks_due_date', 'tasks', ['due_date'])

    # Composite index for priority and date
    op.create_index('idx_tasks_priority_due_date', 'tasks', ['priority', 'due_date'])

    # Index for category searches
    op.create_index('idx_tasks_category', 'tasks', ['category'])

    # GIN index for full-text search
    op.execute(
        'CREATE INDEX idx_tasks_search_gin ON tasks USING GIN(search_vector)'
    )

    # Add trigger for automatically updating search vector
    op.execute("""
        CREATE TRIGGER tasks_search_vector_update
            BEFORE INSERT OR UPDATE ON tasks
            FOR EACH ROW
            EXECUTE FUNCTION
                tsvector_update_trigger(
                    search_vector, 'pg_catalog.english',
                    name, category, priority
                )
    """)


def downgrade() -> None:
    op.execute('DROP TRIGGER IF EXISTS tasks_search_vector_update ON tasks')
    op.drop_index('idx_tasks_search_gin')
    op.drop_index('idx_tasks_due_date')
    op.drop_index('idx_tasks_priority_due_date')
    op.drop_index('idx_tasks_category')
