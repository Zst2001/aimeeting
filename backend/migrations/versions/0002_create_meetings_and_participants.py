"""create meetings and participants

Revision ID: 0002_create_meeting_participants
Revises: 0001_create_users
Create Date: 2026-09-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "0002_create_meeting_participants"
down_revision = "0001_create_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "meetings",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("tencent_meeting_id", sa.String(length=128), nullable=False),
        sa.Column("meeting_code", sa.String(length=64), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("creator_user_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("tencent_creator_userid", sa.String(length=128), nullable=True),
        sa.Column("start_time", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("end_time", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("meeting_status", sa.String(length=32), server_default=sa.text("'SCHEDULED'"), nullable=False),
        sa.Column("ai_minutes_enabled", mysql.TINYINT(display_width=1), server_default=sa.text("0"), nullable=False),
        sa.Column("ai_minutes_enabled_by", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("ai_minutes_enabled_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("minutes_status", sa.String(length=32), server_default=sa.text("'DISABLED'"), nullable=False),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("updated_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.ForeignKeyConstraint(["creator_user_id"], ["users.id"], name="fk_meetings_creator"),
        sa.ForeignKeyConstraint(["ai_minutes_enabled_by"], ["users.id"], name="fk_meetings_ai_enabled_by"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tencent_meeting_id", name="uk_meetings_tencent_meeting_id"),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )
    op.create_index("idx_meetings_creator", "meetings", ["creator_user_id"], unique=False)
    op.create_index("idx_meetings_start_time", "meetings", ["start_time"], unique=False)
    op.create_index("idx_meetings_status", "meetings", ["meeting_status"], unique=False)
    op.create_index("idx_meetings_minutes_status", "meetings", ["minutes_status"], unique=False)

    op.create_table(
        "meeting_participants",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("meeting_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("tencent_userid", sa.String(length=128), nullable=True),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("is_internal", mysql.TINYINT(display_width=1), server_default=sa.text("0"), nullable=False),
        sa.Column("join_time", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("leave_time", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], name="fk_participants_meeting", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_participants_user"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )
    op.create_index("idx_participants_meeting", "meeting_participants", ["meeting_id"], unique=False)
    op.create_index("idx_participants_user", "meeting_participants", ["user_id"], unique=False)
    op.create_index("idx_participants_tencent_userid", "meeting_participants", ["tencent_userid"], unique=False)


def downgrade() -> None:
    # The foreign keys use these indexes on MySQL, so remove each table as a
    # whole rather than attempting to drop an index before its FK is gone.
    op.drop_table("meeting_participants")

    op.drop_table("meetings")
