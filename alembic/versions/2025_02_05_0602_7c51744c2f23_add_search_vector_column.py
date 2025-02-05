"""add_search_vector_column

Revision ID: 7c51744c2f23
Revises: cd63887fb992
Create Date: 2025-02-05 06:02:54.104697+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7c51744c2f23'
down_revision: Union[str, None] = 'cd63887fb992'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add btree_gin extension
    op.execute('CREATE EXTENSION IF NOT EXISTS btree_gin')

    # Add the search vector column
    op.add_column('tasks',
                  sa.Column('search_vector', postgresql.TSVECTOR)
                  )

    # Update existing rows to populate search vector
    op.execute("""
        UPDATE tasks
        SET search_vector = 
            setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(category, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(priority, '')), 'C')
    """)


def downgrade() -> None:
    op.drop_column('tasks', 'search_vector')
