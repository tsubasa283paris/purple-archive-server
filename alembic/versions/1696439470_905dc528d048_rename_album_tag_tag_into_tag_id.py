"""Rename album_tag.tag into tag_id

Revision ID: 905dc528d048
Revises: cf68beedb410
Create Date: 2023-10-05 02:11:10.734737

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '905dc528d048'
down_revision: Union[str, None] = 'cf68beedb410'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('album_tag', sa.Column('tag_id', sa.Integer(), nullable=False))
    op.drop_constraint('album_tag_tag_fkey', 'album_tag', type_='foreignkey')
    op.create_foreign_key(None, 'album_tag', 'tag', ['tag_id'], ['id'])
    op.drop_column('album_tag', 'tag')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('album_tag', sa.Column('tag', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'album_tag', type_='foreignkey')
    op.create_foreign_key('album_tag_tag_fkey', 'album_tag', 'tag', ['tag'], ['id'])
    op.drop_column('album_tag', 'tag_id')
    # ### end Alembic commands ###
