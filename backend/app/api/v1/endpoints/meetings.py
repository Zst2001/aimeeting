from fastapi import APIRouter, Depends, Path, Query

from app.api.dependencies import get_current_user, get_meeting_service
from app.core.logging import request_id_context
from app.db.models.meeting import MeetingStatus, MinutesStatus
from app.db.models.user import User
from app.schemas.meeting import (
    ApiSuccessMeetingDetailResponse,
    ApiSuccessMeetingListResponse,
    MeetingScope,
)
from app.services.meeting_service import MeetingService


router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.get("", response_model=ApiSuccessMeetingListResponse)
def list_meetings(
    scope: MeetingScope = Query(default=MeetingScope.HOSTED),
    meeting_status: MeetingStatus | None = Query(default=None),
    minutes_status: MinutesStatus | None = Query(default=None),
    keyword: str | None = Query(default=None, max_length=255),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    meeting_service: MeetingService = Depends(get_meeting_service),
) -> dict[str, object]:
    data = meeting_service.list_meetings(
        current_user=current_user,
        scope=scope,
        meeting_status=meeting_status,
        minutes_status=minutes_status,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return {"code": 0, "message": "ok", "data": data, "request_id": request_id_context.get()}


@router.get("/{meeting_id}", response_model=ApiSuccessMeetingDetailResponse)
def get_meeting_detail(
    meeting_id: int = Path(ge=1),
    current_user: User = Depends(get_current_user),
    meeting_service: MeetingService = Depends(get_meeting_service),
) -> dict[str, object]:
    data = meeting_service.get_meeting_detail(meeting_id=meeting_id, current_user=current_user)
    return {"code": 0, "message": "ok", "data": data, "request_id": request_id_context.get()}
