"""test

Revision ID: 12b8c1b6fe1f
Revises: 25473f68de7b
Create Date: 2015-07-25 09:59:28.277122

"""

# revision identifiers, used by Alembic.
revision = '12b8c1b6fe1f'
down_revision = '25473f68de7b'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('votes',
        sa.Column('picture', sa.Text(), nullable=True))

def downgrade():
    pass
