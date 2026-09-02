"""create users

Revision ID: 0001_create_users
Revises:
Create Date: 2026-09-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "0001_create_users"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("employee_no", sa.String(length=64), nullable=True),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("tencent_userid", sa.String(length=128), nullable=True),
        sa.Column("role", sa.String(length=16), server_default="USER", nullable=False),
        sa.Column("status", sa.String(length=16), server_default="ACTIVE", nullable=False),
        sa.Column("last_login_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("updated_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", name="uk_users_username"),
        sa.UniqueConstraint("employee_no", name="uk_users_employee_no"),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )
    op.create_index("idx_users_tencent_userid", "users", ["tencent_userid"], unique=False)
    op.create_index("idx_users_role_status", "users", ["role", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_users_role_status", table_name="users")
    op.drop_index("idx_users_tencent_userid", table_name="users")
    op.drop_table("users")
