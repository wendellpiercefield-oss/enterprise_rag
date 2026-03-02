"""add documents and jobs

Revision ID: c11d75fa8a89
Revises: 7a3582b206df
Create Date: 2026-03-01 12:10:28.110363

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c11d75fa8a89'
down_revision: Union[str, Sequence[str], None] = '7a3582b206df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
