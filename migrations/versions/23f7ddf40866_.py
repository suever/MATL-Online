"""empty message

Revision ID: 23f7ddf40866
Revises: 5688ce609630
Create Date: 2018-01-06 13:23:34.656654

"""

# revision identifiers, used by Alembic.
revision = '23f7ddf40866'
down_revision = '5688ce609630'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('releases') as batch_op:
        batch_op.alter_column('date',
                              existing_type=sa.DATETIME(),
                              nullable=False)

        batch_op.alter_column('tag',
                              existing_type=sa.VARCHAR(),
                              nullable=False)


def downgrade():
    with op.batch_alter_table('releases') as batch_op:
        batch_op.alter_column('tag',
                              existing_type=sa.VARCHAR(),
                              nullable=True)

        batch_op.alter_column('date',
                              existing_type=sa.DATETIME(),
                              nullable=True)
