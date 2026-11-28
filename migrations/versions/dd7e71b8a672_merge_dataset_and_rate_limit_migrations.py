"""merge dataset and rate limit migrations

Revision ID: dd7e71b8a672
Revises: 002, afea33b52537
Create Date: 2026-11-28 18:57:52.900605

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dd7e71b8a672'
down_revision = ('002', 'afea33b52537')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
