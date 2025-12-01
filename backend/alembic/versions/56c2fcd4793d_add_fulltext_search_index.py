"""add_fulltext_search_index

Revision ID: 56c2fcd4793d
Revises: f56b995b94be
Create Date: 2025-11-29 09:38:45.184193

为 news 表添加 PostgreSQL 全文搜索索引
支持标题和内容的全文检索
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '56c2fcd4793d'
down_revision: Union[str, Sequence[str], None] = 'f56b995b94be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    添加全文搜索支持
    1. 添加 search_vector 列存储 tsvector
    2. 创建 GIN 索引加速搜索
    3. 创建触发器自动更新 search_vector
    """
    # 添加 search_vector 列
    op.execute(
        "ALTER TABLE news ADD COLUMN IF NOT EXISTS search_vector tsvector"
    )
    
    # 更新现有数据的 search_vector
    op.execute("""
        UPDATE news 
        SET search_vector = 
            setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(summary, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(content, '')), 'C')
    """)
    
    # 创建 GIN 索引
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_news_search_vector ON news USING GIN(search_vector)"
    )
    
    # 创建触发器函数，自动更新 search_vector
    op.execute("""
        CREATE OR REPLACE FUNCTION news_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.summary, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(NEW.content, '')), 'C');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql
    """)
    
    # 删除旧触发器（如果存在）
    op.execute("DROP TRIGGER IF EXISTS news_search_vector_trigger ON news")
    
    # 创建触发器
    op.execute("""
        CREATE TRIGGER news_search_vector_trigger
        BEFORE INSERT OR UPDATE ON news
        FOR EACH ROW EXECUTE FUNCTION news_search_vector_update()
    """)
    
    # 创建 source 和 category 索引用于筛选
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_news_source ON news(source)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_news_category ON news(category)"
    )


def downgrade() -> None:
    """
    移除全文搜索支持
    """
    # 删除触发器
    op.execute("DROP TRIGGER IF EXISTS news_search_vector_trigger ON news")
    
    # 删除触发器函数
    op.execute("DROP FUNCTION IF EXISTS news_search_vector_update()")
    
    # 删除索引
    op.execute("DROP INDEX IF EXISTS idx_news_search_vector")
    op.execute("DROP INDEX IF EXISTS idx_news_source")
    op.execute("DROP INDEX IF EXISTS idx_news_category")
    
    # 删除列
    op.execute("ALTER TABLE news DROP COLUMN IF EXISTS search_vector")
