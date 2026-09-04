"""create meeting permissions

Revision ID: 0003_create_meeting_permissions
Revises: 0002_create_meeting_participants
Create Date: 2026-09-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "0003_create_meeting_permissions"
down_revision = "0002_create_meeting_participants"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "meeting_permissions",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("meeting_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("permission", sa.String(length=16), server_default=sa.text("'VIEW'"), nullable=False),
        sa.Column("granted_by", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], name="fk_permission_meeting", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_permission_user", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by"], ["users.id"], name="fk_permission_granted_by"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id", "user_id", "permission", name="uk_meeting_user_permission"),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )
    op.create_index("idx_permissions_user", "meeting_permissions", ["user_id"], unique=False)


def downgrade() -> None:
    # MySQL uses idx_permissions_user to enforce fk_permission_user; dropping
    # the table safely removes the dependent foreign keys and indexes together.
    op.drop_table("meeting_permissions")
