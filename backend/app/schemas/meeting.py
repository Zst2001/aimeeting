from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from app.db.models.meeting import MeetingStatus, MinutesStatus
class MeetingScope(str, Enum):
    HOSTED = "hosted"
    JOINED = "joined"
    SHARED = "shared"
    ALL = "all"


class MeetingHostResponse(BaseModel):
    id: int
    display_name: str


class MeetingParticipantResponse(BaseModel):
    user_id: int | None
    display_name: str
    is_internal: bool


class MeetingPermissionResponse(BaseModel):
    can_view: bool
    can_edit_minutes: bool
    can_regenerate: bool
    can_manage_permissions: bool
    can_view_ai_versions: bool


class MeetingListItemResponse(BaseModel):
    id: int
    subject: str
    meeting_code: str | None
    host: MeetingHostResponse | None
    start_time: datetime | None
    end_time: datetime | None
    meeting_status: MeetingStatus
    ai_minutes_enabled: bool
    minutes_status: MinutesStatus
    my_role: str


class MeetingListDataResponse(BaseModel):
    items: list[MeetingListItemResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class MeetingDetailResponse(BaseModel):
    id: int
    tencent_meeting_id: str
    meeting_code: str | None
    subject: str
    host: MeetingHostResponse | None
    participants: list[MeetingParticipantResponse]
    start_time: datetime | None
    end_time: datetime | None
    meeting_status: MeetingStatus
    ai_minutes_enabled: bool
    minutes_status: MinutesStatus
    permissions: MeetingPermissionResponse


class ApiSuccessMeetingListResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: MeetingListDataResponse
    request_id: str


class ApiSuccessMeetingDetailResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: MeetingDetailResponse
    request_id: str
