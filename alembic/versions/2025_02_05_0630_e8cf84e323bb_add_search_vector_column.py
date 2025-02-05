"""add_search_vector_column

Revision ID: e8cf84e323bb
Revises: 5b1818401bfa
Create Date: 2025-02-05 06:30:27.270917+00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e8cf84e323bb'
down_revision: Union[str, None] = '5b1818401bfa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add the search_vector column
    op.add_column('tasks',
        sa.Column('search_vector', postgresql.TSVECTOR)
    )

    # Create GIN index for search_vector
    op.create_index(
        'idx_task_search_vector',
        'tasks',
        ['search_vector'],
        postgresql_using='gin'
    )

    # Create function to generate search vector
    op.execute("""
        CREATE OR REPLACE FUNCTION tasks_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.category, '')), 'B') ||
                setweight(to_tsvector('english', COALESCE(NEW.priority, '')), 'C');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger
    op.execute("""
        CREATE TRIGGER tasks_search_vector_trigger
            BEFORE INSERT OR UPDATE ON tasks
            FOR EACH ROW
            EXECUTE FUNCTION tasks_search_vector_update();
    """)

    # Update existing rows
    op.execute("""
        UPDATE tasks
        SET search_vector = 
            setweight(to_tsvector('english', COALESCE(name, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(category, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(priority, '')), 'C');
    """)

def downgrade() -> None:
    # Drop trigger first
    op.execute("DROP TRIGGER IF EXISTS tasks_search_vector_trigger ON tasks")

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS tasks_search_vector_update")

    # Drop index
    op.drop_index('idx_task_search_vector', table_name='tasks')

    # Drop column
    op.drop_column('tasks', 'search_vector')