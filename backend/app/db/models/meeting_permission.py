from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.datetime import utc_now


if TYPE_CHECKING:
    from app.db.models.meeting import Meeting
    from app.db.models.user import User


class MeetingPermissionType(str, Enum):
    VIEW = "VIEW"


class MeetingPermission(Base):
    __tablename__ = "meeting_permissions"
    __table_args__ = (
        UniqueConstraint("meeting_id", "user_id", "permission", name="uk_meeting_user_permission"),
        Index("idx_permissions_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("meetings.id", name="fk_permission_meeting", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("users.id", name="fk_permission_user", ondelete="CASCADE"), nullable=False
    )
    permission: Mapped[str] = mapped_column(
        String(16), nullable=False, default=MeetingPermissionType.VIEW.value, server_default=MeetingPermissionType.VIEW.value
    )
    granted_by: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("users.id", name="fk_permission_granted_by"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False, default=utc_now)

    meeting: Mapped[Meeting] = relationship("Meeting", back_populates="permissions", foreign_keys=[meeting_id])
    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
    granted_by_user: Mapped[User] = relationship("User", foreign_keys=[granted_by])
