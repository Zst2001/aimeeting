from dataclasses import dataclass
from enum import Enum

from app.db.models.meeting import Meeting
from app.db.models.user import User, UserRole
from app.repositories.participant_repository import ParticipantRepository
from app.repositories.permission_repository import PermissionRepository


class MeetingRelation(str, Enum):
    HOST = "HOST"
    PARTICIPANT = "PARTICIPANT"
    SHARED = "SHARED"
    ADMIN = "ADMIN"
    NONE = "NONE"


@dataclass(frozen=True)
class MeetingPermissionSnapshot:
    can_view: bool
    can_toggle_ai_minutes: bool
    can_edit_minutes: bool
    can_regenerate: bool
    can_manage_permissions: bool
    can_view_ai_versions: bool


@dataclass(frozen=True)
class _MeetingAccess:
    is_admin: bool
    is_host: bool
    is_participant: bool
    is_shared: bool


class PermissionService:
    """The single business-policy boundary for persisted meeting access."""

    def __init__(
        self,
        participant_repository: ParticipantRepository,
        permission_repository: PermissionRepository,
    ) -> None:
        self.participant_repository = participant_repository
        self.permission_repository = permission_repository

    def can_view_meeting(self, *, meeting: Meeting, user: User) -> bool:
        return self.get_permission_snapshot(meeting=meeting, user=user).can_view

    def can_toggle_ai_minutes(self, *, meeting: Meeting, user: User) -> bool:
        return self.get_permission_snapshot(meeting=meeting, user=user).can_toggle_ai_minutes

    def can_edit_minutes(self, *, meeting: Meeting, user: User) -> bool:
        return self.get_permission_snapshot(meeting=meeting, user=user).can_edit_minutes

    def can_regenerate_minutes(self, *, meeting: Meeting, user: User) -> bool:
        return self.get_permission_snapshot(meeting=meeting, user=user).can_regenerate

    def can_manage_permissions(self, *, meeting: Meeting, user: User) -> bool:
        return self.get_permission_snapshot(meeting=meeting, user=user).can_manage_permissions

    def can_view_ai_versions(self, *, meeting: Meeting, user: User) -> bool:
        return self.get_permission_snapshot(meeting=meeting, user=user).can_view_ai_versions

    def resolve_meeting_relation(self, *, meeting: Meeting, user: User) -> MeetingRelation:
        access = self._resolve_access(meeting=meeting, user=user)
        if access.is_host:
            return MeetingRelation.HOST
        if access.is_participant:
            return MeetingRelation.PARTICIPANT
        if access.is_shared:
            return MeetingRelation.SHARED
        if access.is_admin:
            return MeetingRelation.ADMIN
        return MeetingRelation.NONE

    def get_permission_snapshot(self, *, meeting: Meeting, user: User) -> MeetingPermissionSnapshot:
        # Administrator authorization is absolute and must not depend on relation queries.
        if user.role == UserRole.ADMIN.value:
            return _FULL_ACCESS
        access = self._resolve_access(meeting=meeting, user=user)

        if access.is_host:
            return _FULL_ACCESS
        if access.is_participant or access.is_shared:
            return _VIEW_ONLY_ACCESS
        return _NO_ACCESS

    def _resolve_access(self, *, meeting: Meeting, user: User) -> _MeetingAccess:
        # Resolve relationship facts once per snapshot instead of executing a query per capability.
        return _MeetingAccess(
            is_admin=user.role == UserRole.ADMIN.value,
            is_host=meeting.creator_user_id == user.id,
            is_participant=self.participant_repository.is_participant(meeting.id, user.id),
            is_shared=self.permission_repository.has_view_permission(meeting.id, user.id),
        )


_FULL_ACCESS = MeetingPermissionSnapshot(True, True, True, True, True, True)
_VIEW_ONLY_ACCESS = MeetingPermissionSnapshot(True, False, False, False, False, False)
_NO_ACCESS = MeetingPermissionSnapshot(False, False, False, False, False, False)
