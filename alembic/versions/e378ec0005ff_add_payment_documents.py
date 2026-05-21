"""add_payment_documents

Revision ID: e378ec0005ff
Revises: f57dee18c85a
Create Date: 2026-05-21 10:29:36.511178

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a4b5c6d7e8f9'
down_revision: Union[str, Sequence[str], None] = 'f57dee18c85a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('rut_url', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('cedula_url', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'rut_url')
    op.drop_column('users', 'cedula_url')