"""Initial migration - create all tables

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Create chats table
    op.create_table(
        'chats',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('access_hash', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('public_url', sa.String(512), nullable=True),
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('chat_type', sa.String(20), nullable=False),
        sa.Column('member_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('topic', sa.String(255), nullable=True),
        sa.Column('discovery_source', sa.String(255), nullable=True),
        sa.Column('discovered_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_check_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('avatar_hash', sa.String(64), nullable=True),
        sa.Column('quality_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('popularity_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('activity_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('growth_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('health_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id'),
        sa.UniqueConstraint('username'),
    )

    # Create indexes for chats
    op.create_index('idx_chats_username', 'chats', ['username'], postgresql_where='username IS NOT NULL')
    op.create_index('idx_chats_type', 'chats', ['chat_type'])
    op.create_index('idx_chats_language', 'chats', ['language'], postgresql_where='language IS NOT NULL')
    op.create_index('idx_chats_topic', 'chats', ['topic'], postgresql_where='topic IS NOT NULL')
    op.create_index('idx_chats_discovered_at', 'chats', ['discovered_at'])
    op.create_index('idx_chats_next_check_at', 'chats', ['next_check_at'], postgresql_where='next_check_at IS NOT NULL')
    op.create_index('idx_chats_quality_score', 'chats', ['quality_score'])
    op.create_index('idx_chats_is_active', 'chats', ['is_active'], postgresql_where='is_active = TRUE')
    op.create_index('idx_chats_member_count', 'chats', ['member_count'])

    # Create FTS index
    op.execute("""
        CREATE INDEX idx_chats_fts ON chats USING GIN (
            to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(description, '') || ' ' || coalesce(topic, ''))
        )
    """)

    # Create discovery_sources table
    op.create_table(
        'discovery_sources',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('url', sa.String(1024), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('run_interval', sa.Interval(), nullable=False),
        sa.Column('total_found', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_errors', sa.Integer(), server_default='0', nullable=False),
        sa.Column('config', postgresql.JSONB(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # Create url_queue table
    op.create_table(
        'url_queue',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('url', sa.String(1024), nullable=False),
        sa.Column('normalized_url', sa.String(1024), nullable=False),
        sa.Column('url_hash', sa.String(64), nullable=False),
        sa.Column('source', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), server_default='pending', nullable=False),
        sa.Column('priority', sa.SmallInteger(), server_default='0', nullable=False),
        sa.Column('attempts', sa.SmallInteger(), server_default='0', nullable=False),
        sa.Column('max_attempts', sa.SmallInteger(), server_default='3', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url_hash'),
    )

    # Create indexes for url_queue
    op.create_index('idx_url_queue_status', 'url_queue', ['status'], postgresql_where="status IN ('pending', 'processing')")
    op.create_index('idx_url_queue_hash', 'url_queue', ['url_hash'])
    op.create_index('idx_url_queue_priority', 'url_queue', ['priority', 'created_at'], postgresql_where="status = 'pending'")

    # Create crawl_logs table
    op.create_table(
        'crawl_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=True),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['discovery_sources.id'], ondelete='SET NULL'),
    )

    # Create indexes for crawl_logs
    op.create_index('idx_crawl_logs_chat_id', 'crawl_logs', ['chat_id'])
    op.create_index('idx_crawl_logs_created_at', 'crawl_logs', ['created_at'])
    op.create_index('idx_crawl_logs_status', 'crawl_logs', ['status'])

    # Create statistics_snapshots table
    op.create_table(
        'statistics_snapshots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('total_chats', sa.Integer(), server_default='0', nullable=False),
        sa.Column('new_today', sa.Integer(), server_default='0', nullable=False),
        sa.Column('new_this_week', sa.Integer(), server_default='0', nullable=False),
        sa.Column('new_this_month', sa.Integer(), server_default='0', nullable=False),
        sa.Column('processed_urls', sa.Integer(), server_default='0', nullable=False),
        sa.Column('queue_size', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('duplicate_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('broken_links', sa.Integer(), server_default='0', nullable=False),
        sa.Column('avg_discovery_speed', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('avg_indexing_speed', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('flood_wait_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('source_stats', postgresql.JSONB(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('snapshot_date'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('statistics_snapshots')
    op.drop_table('crawl_logs')
    op.drop_table('url_queue')
    op.drop_table('discovery_sources')
    op.drop_table('chats')
