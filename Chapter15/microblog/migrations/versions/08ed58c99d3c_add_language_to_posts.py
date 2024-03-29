"""add language to posts

Revision ID: 08ed58c99d3c
Revises: df9c10872478
Create Date: 2021-12-15 11:36:23.142146

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '08ed58c99d3c'
down_revision = 'df9c10872478'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('post', sa.Column('language', sa.String(length=5), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('post', 'language')
    # ### end Alembic commands ###
