from math import ceil

from app.core.error_codes import MEETING_NOT_FOUND, PERMISSION_ADMIN_REQUIRED, PERMISSION_MEETING_ACCESS_DENIED
from app.core.exceptions import AppException
from app.db.models.meeting import Meeting, MeetingStatus, MinutesStatus
from app.db.models.user import User, UserRole
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.participant_repository import ParticipantRepository
from app.repositories.permission_repository import PermissionRepository
from app.schemas.meeting import (
    MeetingDetailResponse,
    MeetingHostResponse,
    MeetingListDataResponse,
    MeetingListItemResponse,
    MeetingParticipantResponse,
    MeetingPermissionResponse,
    MeetingScope,
)
from app.services.permission_service import MeetingRelation, PermissionService


class MeetingService:
    """Coordinates read-only meeting use cases and centralized access policy."""

    def __init__(
        self,
        meeting_repository: MeetingRepository,
        participant_repository: ParticipantRepository,
        permission_repository: PermissionRepository,
        permission_service: PermissionService,
    ) -> None:
        self.meeting_repository = meeting_repository
        self.participant_repository = participant_repository
        self.permission_repository = permission_repository
        self.permission_service = permission_service

    def list_meetings(
        self,
        *,
        current_user: User,
        scope: MeetingScope = MeetingScope.HOSTED,
        meeting_status: MeetingStatus | None = None,
        minutes_status: MinutesStatus | None = None,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> MeetingListDataResponse:
        self._ensure_scope_allowed(current_user=current_user, scope=scope)
        offset = (page - 1) * page_size
        meetings = self.meeting_repository.list_meetings(
            user_id=current_user.id,
            scope=scope.value,
            meeting_status=meeting_status,
            minutes_status=minutes_status,
            keyword=keyword,
            offset=offset,
            limit=page_size,
        )
        total = self.meeting_repository.count_meetings(
            user_id=current_user.id,
            scope=scope.value,
            meeting_status=meeting_status,
            minutes_status=minutes_status,
            keyword=keyword,
        )

        meeting_ids = [meeting.id for meeting in meetings]
        participated_ids = self.participant_repository.get_participated_meeting_ids(current_user.id, meeting_ids)
        shared_ids = self.permission_repository.get_view_permission_meeting_ids(current_user.id, meeting_ids)
        items = [
            _list_item(
                meeting=meeting,
                relation=_list_relation(
                    meeting=meeting,
                    current_user=current_user,
                    participated_ids=participated_ids,
                    shared_ids=shared_ids,
                ),
            )
            for meeting in meetings
        ]
        return MeetingListDataResponse(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if total else 0,
        )

    def get_meeting_detail(self, *, meeting_id: int, current_user: User) -> MeetingDetailResponse:
        meeting = self.meeting_repository.get_by_id(meeting_id)
        if meeting is None:
            raise AppException("会议不存在", MEETING_NOT_FOUND, 404)

        snapshot = self.permission_service.get_permission_snapshot(meeting=meeting, user=current_user)
        if not snapshot.can_view:
            raise AppException("无会议访问权限", PERMISSION_MEETING_ACCESS_DENIED, 403)

        participants = self.participant_repository.list_by_meeting(meeting.id)
        return MeetingDetailResponse(
            id=meeting.id,
            tencent_meeting_id=meeting.tencent_meeting_id,
            meeting_code=meeting.meeting_code,
            subject=meeting.subject,
            host=_host_response(meeting),
            participants=[
                MeetingParticipantResponse(
                    user_id=participant.user_id,
                    display_name=participant.display_name,
                    is_internal=participant.is_internal,
                )
                for participant in participants
            ],
            start_time=meeting.start_time,
            end_time=meeting.end_time,
            meeting_status=MeetingStatus(meeting.meeting_status),
            ai_minutes_enabled=meeting.ai_minutes_enabled,
            minutes_status=MinutesStatus(meeting.minutes_status),
            permissions=MeetingPermissionResponse(
                can_view=snapshot.can_view,
                can_edit_minutes=snapshot.can_edit_minutes,
                can_regenerate=snapshot.can_regenerate,
                can_manage_permissions=snapshot.can_manage_permissions,
                can_view_ai_versions=snapshot.can_view_ai_versions,
            ),
        )

    @staticmethod
    def _ensure_scope_allowed(*, current_user: User, scope: MeetingScope) -> None:
        if scope is MeetingScope.ALL and current_user.role != UserRole.ADMIN.value:
            raise AppException("需要管理员权限", PERMISSION_ADMIN_REQUIRED, 403)


def _list_item(*, meeting: Meeting, relation: MeetingRelation) -> MeetingListItemResponse:
    return MeetingListItemResponse(
        id=meeting.id,
        subject=meeting.subject,
        meeting_code=meeting.meeting_code,
        host=_host_response(meeting),
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        meeting_status=MeetingStatus(meeting.meeting_status),
        ai_minutes_enabled=meeting.ai_minutes_enabled,
        minutes_status=MinutesStatus(meeting.minutes_status),
        my_role=relation,
    )


def _host_response(meeting: Meeting) -> MeetingHostResponse | None:
    if meeting.creator is None:
        return None
    return MeetingHostResponse(id=meeting.creator.id, display_name=meeting.creator.display_name)


def _list_relation(
    *,
    meeting: Meeting,
    current_user: User,
    participated_ids: set[int],
    shared_ids: set[int],
) -> MeetingRelation:
    if meeting.creator_user_id == current_user.id:
        return MeetingRelation.HOST
    if meeting.id in participated_ids:
        return MeetingRelation.PARTICIPANT
    if meeting.id in shared_ids:
        return MeetingRelation.SHARED
    if current_user.role == UserRole.ADMIN.value:
        return MeetingRelation.ADMIN
    return MeetingRelation.NONE
