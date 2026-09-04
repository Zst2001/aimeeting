from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.datetime import utc_now


if TYPE_CHECKING:
    from app.db.models.meeting import Meeting
    from app.db.models.user import User


class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"
    __table_args__ = (
        Index("idx_participants_meeting", "meeting_id"),
        Index("idx_participants_user", "user_id"),
        Index("idx_participants_tencent_userid", "tencent_userid"),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("meetings.id", name="fk_participants_meeting", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("users.id", name="fk_participants_user"), nullable=True
    )
    tencent_userid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    join_time: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    leave_time: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False, default=utc_now)

    meeting: Mapped[Meeting] = relationship("Meeting", back_populates="participants", foreign_keys=[meeting_id])
    user: Mapped[User | None] = relationship("User", foreign_keys=[user_id])
