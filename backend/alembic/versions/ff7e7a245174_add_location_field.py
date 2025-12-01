"""add_location_field

Revision ID: ff7e7a245174
Revises: 56c2fcd4793d
Create Date: 2025-11-29 10:04:41.415200

为 news 表添加 location 字段，用于存储地理位置信息
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ff7e7a245174'
down_revision: Union[str, Sequence[str], None] = '56c2fcd4793d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加 location 字段"""
    op.add_column('news', sa.Column('location', sa.JSON(), nullable=True))


def downgrade() -> None:
    """移除 location 字段"""
    op.drop_column('news', 'location')
