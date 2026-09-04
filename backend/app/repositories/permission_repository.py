from enum import Enum

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.db.models.meeting_permission import MeetingPermission, MeetingPermissionType


class PermissionRepository:
    """Read access to persisted meeting grants; grant/revoke belongs to a later task."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def has_permission(
        self,
        meeting_id: int,
        user_id: int,
        permission: MeetingPermissionType | str,
    ) -> bool:
        permission_value = permission.value if isinstance(permission, Enum) else permission
        statement = select(
            exists().where(
                MeetingPermission.meeting_id == meeting_id,
                MeetingPermission.user_id == user_id,
                MeetingPermission.permission == permission_value,
            )
        )
        return bool(self.session.scalar(statement))

    def has_view_permission(self, meeting_id: int, user_id: int) -> bool:
        return self.has_permission(meeting_id, user_id, MeetingPermissionType.VIEW)

    def get_view_permission_meeting_ids(self, user_id: int, meeting_ids: list[int]) -> set[int]:
        """Return VIEW grants in one query for a meeting list."""

        if not meeting_ids:
            return set()
        statement = (
            select(MeetingPermission.meeting_id)
            .where(
                MeetingPermission.user_id == user_id,
                MeetingPermission.meeting_id.in_(meeting_ids),
                MeetingPermission.permission == MeetingPermissionType.VIEW.value,
            )
            .distinct()
        )
        return set(self.session.scalars(statement))
