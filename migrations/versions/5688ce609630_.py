"""empty message

Revision ID: 5688ce609630
Revises: e351c0605462
Create Date: 2016-08-19 19:07:33.675314

"""

# revision identifiers, used by Alembic.
revision = '5688ce609630'
down_revision = 'e351c0605462'

import sqlalchemy as sa
from alembic import op


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('documentation_link',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('link', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('documentation_link')
    ### end Alembic commands ###
