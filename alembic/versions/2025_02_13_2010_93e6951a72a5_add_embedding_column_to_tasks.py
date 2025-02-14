"""Add embedding column to tasks

Revision ID: 93e6951a72a5
Revises: b409ddfb640a
Create Date: 2025-02-13 20:10:09.792172+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '93e6951a72a5'
down_revision: Union[str, None] = 'b409ddfb640a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add vector extension if not exists
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Add embedding column (vector of 1536 floats)
    op.add_column('tasks',
                  sa.Column('embedding',
                            Vector(1536),  # Use Vector instead of postgresql.VECTOR
                            nullable=True
                            )
                  )

    # Create index for efficient similarity search
    op.execute(
        'CREATE INDEX task_embedding_idx ON tasks USING hnsw (embedding vector_cosine_ops)'
    )


def downgrade() -> None:
    # Drop index first
    op.execute('DROP INDEX IF EXISTS task_embedding_idx')

    # Drop column
    op.drop_column('tasks', 'embedding')
