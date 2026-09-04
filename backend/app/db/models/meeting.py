from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.datetime import utc_now


if TYPE_CHECKING:
    from app.db.models.meeting_participant import MeetingParticipant
    from app.db.models.meeting_permission import MeetingPermission
    from app.db.models.user import User


class MeetingStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    ENDED = "ENDED"


class MinutesStatus(str, Enum):
    DISABLED = "DISABLED"
    WAITING_MEETING_END = "WAITING_MEETING_END"
    WAITING_RECORDING = "WAITING_RECORDING"
    WAITING_TRANSCRIPT = "WAITING_TRANSCRIPT"
    AI_PROCESSING = "AI_PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class Meeting(Base):
    __tablename__ = "meetings"
    __table_args__ = (
        UniqueConstraint("tencent_meeting_id", name="uk_meetings_tencent_meeting_id"),
        Index("idx_meetings_creator", "creator_user_id"),
        Index("idx_meetings_start_time", "start_time"),
        Index("idx_meetings_status", "meeting_status"),
        Index("idx_meetings_minutes_status", "minutes_status"),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    tencent_meeting_id: Mapped[str] = mapped_column(String(128), nullable=False)
    meeting_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)

    creator_user_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("users.id", name="fk_meetings_creator"), nullable=True
    )
    tencent_creator_userid: Mapped[str | None] = mapped_column(String(128), nullable=True)

    start_time: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    meeting_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=MeetingStatus.SCHEDULED.value, server_default=MeetingStatus.SCHEDULED.value
    )

    ai_minutes_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    ai_minutes_enabled_by: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("users.id", name="fk_meetings_ai_enabled_by"), nullable=True
    )
    ai_minutes_enabled_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)

    minutes_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=MinutesStatus.DISABLED.value, server_default=MinutesStatus.DISABLED.value
    )
    created_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False, default=utc_now, onupdate=utc_now)

    creator: Mapped[User | None] = relationship("User", foreign_keys=[creator_user_id])
    ai_minutes_enabled_by_user: Mapped[User | None] = relationship(
        "User", foreign_keys=[ai_minutes_enabled_by]
    )
    participants: Mapped[list[MeetingParticipant]] = relationship(
        "MeetingParticipant", back_populates="meeting", passive_deletes=True
    )
    permissions: Mapped[list[MeetingPermission]] = relationship(
        "MeetingPermission", back_populates="meeting", passive_deletes=True
    )
