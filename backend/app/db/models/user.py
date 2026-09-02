from datetime import datetime
from enum import Enum

from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.utils.datetime import utc_now


class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uk_users_username"),
        UniqueConstraint("employee_no", name="uk_users_employee_no"),
        Index("idx_users_tencent_userid", "tencent_userid"),
        Index("idx_users_role_status", "role", "status"),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    employee_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tencent_userid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default=UserRole.USER.value, server_default=UserRole.USER.value)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=UserStatus.ACTIVE.value, server_default=UserStatus.ACTIVE.value)
    last_login_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False, default=utc_now, onupdate=utc_now)
