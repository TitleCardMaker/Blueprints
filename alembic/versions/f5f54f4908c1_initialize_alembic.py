"""Initialize Alembic

Revision ID: f5f54f4908c1
Revises: 
Create Date: 2024-03-15 13:52:36.117066

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5f54f4908c1'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('series',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('path_name', sa.String(), nullable=False),
        sa.Column('imdb_id', sa.String(), nullable=True),
        sa.Column('tmdb_id', sa.Integer(), nullable=True),
        sa.Column('tvdb_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('blueprints',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('series_id', sa.Integer(), nullable=False),
        sa.Column('blueprint_number', sa.Integer(), nullable=False),
        sa.Column('creator', sa.String(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('json', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['series_id'], ['series.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('blueprints')
    op.drop_table('series')
