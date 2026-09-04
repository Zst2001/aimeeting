from __future__ import annotations

from enum import Enum

from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.db.models.meeting import Meeting, MeetingStatus, MinutesStatus
from app.db.models.meeting_participant import MeetingParticipant
from app.db.models.meeting_permission import MeetingPermission, MeetingPermissionType


class MeetingRepository:
    """Read queries for meetings and their persisted visibility scopes."""

    _SCOPES = {"hosted", "joined", "shared", "all"}

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, meeting_id: int) -> Meeting | None:
        return self.session.get(Meeting, meeting_id)

    def get_by_tencent_meeting_id(self, tencent_meeting_id: str) -> Meeting | None:
        return self.session.scalar(select(Meeting).where(Meeting.tencent_meeting_id == tencent_meeting_id))

    def list_meetings(
        self,
        *,
        user_id: int,
        scope: str,
        meeting_status: MeetingStatus | str | None = None,
        minutes_status: MinutesStatus | str | None = None,
        keyword: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Meeting]:
        self._validate_pagination(offset=offset, limit=limit)
        conditions = self._conditions(
            user_id=user_id,
            scope=scope,
            meeting_status=meeting_status,
            minutes_status=minutes_status,
            keyword=keyword,
        )
        statement = (
            select(Meeting)
            .where(*conditions)
            .options(selectinload(Meeting.creator))
            .order_by(Meeting.start_time.desc(), Meeting.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement))

    def count_meetings(
        self,
        *,
        user_id: int,
        scope: str,
        meeting_status: MeetingStatus | str | None = None,
        minutes_status: MinutesStatus | str | None = None,
        keyword: str | None = None,
    ) -> int:
        conditions = self._conditions(
            user_id=user_id,
            scope=scope,
            meeting_status=meeting_status,
            minutes_status=minutes_status,
            keyword=keyword,
        )
        return int(self.session.scalar(select(func.count()).select_from(Meeting).where(*conditions)) or 0)

    def _conditions(
        self,
        *,
        user_id: int,
        scope: str,
        meeting_status: MeetingStatus | str | None,
        minutes_status: MinutesStatus | str | None,
        keyword: str | None,
    ) -> list[object]:
        if scope not in self._SCOPES:
            raise ValueError(f"Unsupported meeting scope: {scope}")

        conditions: list[object] = []
        if scope == "hosted":
            conditions.append(Meeting.creator_user_id == user_id)
        elif scope == "joined":
            conditions.append(
                exists(
                    select(1).where(
                        MeetingParticipant.meeting_id == Meeting.id,
                        MeetingParticipant.user_id == user_id,
                    )
                )
            )
        elif scope == "shared":
            conditions.append(
                exists(
                    select(1).where(
                        MeetingPermission.meeting_id == Meeting.id,
                        MeetingPermission.user_id == user_id,
                        MeetingPermission.permission == MeetingPermissionType.VIEW.value,
                    )
                )
            )

        if meeting_status is not None:
            conditions.append(Meeting.meeting_status == _stored_value(meeting_status))
        if minutes_status is not None:
            conditions.append(Meeting.minutes_status == _stored_value(minutes_status))
        if keyword is not None and (normalized_keyword := keyword.strip()):
            pattern = f"%{normalized_keyword}%"
            conditions.append(or_(Meeting.subject.like(pattern), Meeting.meeting_code.like(pattern)))
        return conditions

    @staticmethod
    def _validate_pagination(*, offset: int, limit: int) -> None:
        if offset < 0:
            raise ValueError("offset must be greater than or equal to zero")
        if limit < 0:
            raise ValueError("limit must be greater than or equal to zero")


def _stored_value(value: MeetingStatus | MinutesStatus | str) -> str:
    return value.value if isinstance(value, Enum) else value
