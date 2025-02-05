"""Update due_date to Date type

Revision ID: 78d16308bbef
Revises: 192b40189957
Create Date: 2025-02-04 11:18:49.158254

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '78d16308bbef'
down_revision: Union[str, None] = '192b40189957'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alter `due_date` column with explicit CAST
    op.execute("ALTER TABLE tasks ALTER COLUMN due_date TYPE DATE USING due_date::DATE")


def downgrade() -> None:
    # Revert back to VARCHAR if needed
    op.execute("ALTER TABLE tasks ALTER COLUMN due_date TYPE VARCHAR")
