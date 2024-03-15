"""Add Blueprint Sets

Revision ID: a26e983ea8ca
Revises: f5f54f4908c1
Create Date: 2024-03-15 13:53:27.792554
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a26e983ea8ca'
down_revision: Union[str, None] = 'f5f54f4908c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('sets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('association_table',
        sa.Column('blueprint_id', sa.Integer(), nullable=False),
        sa.Column('set_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['blueprint_id'], ['blueprints.id'], ),
        sa.ForeignKeyConstraint(['set_id'], ['sets.id'], ),
        sa.PrimaryKeyConstraint('blueprint_id', 'set_id')
    )


def downgrade() -> None:
    op.drop_table('association_table')
    op.drop_table('sets')
