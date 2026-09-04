from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from redis import Redis
from sqlalchemy import delete, event
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.error_codes import MEETING_NOT_FOUND, PERMISSION_ADMIN_REQUIRED, PERMISSION_MEETING_ACCESS_DENIED
from app.core.exceptions import AppException
from app.core.security import hash_password
from app.db.models import (
    Meeting,
    MeetingParticipant,
    MeetingPermission,
    MeetingPermissionType,
    MeetingStatus,
    MinutesStatus,
    User,
    UserRole,
)
from app.db.session import SessionLocal, engine
from app.main import app
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.participant_repository import ParticipantRepository
from app.repositories.permission_repository import PermissionRepository
from app.schemas.meeting import MeetingScope
from app.services.meeting_service import MeetingService
from app.services.permission_service import MeetingRelation, PermissionService


@dataclass(frozen=True)
class ApiUser:
    id: int
    username: str
    password: str


@dataclass
class MeetingApiData:
    session: Session
    users: dict[str, ApiUser]
    orm_users: dict[str, User]
    meetings: dict[str, int]
    meeting_ids: list[int]
    user_ids: list[int]


@pytest.fixture(autouse=True)
def require_real_mysql() -> None:
    assert engine.dialect.name == "mysql"


@pytest.fixture
def meeting_api_data() -> MeetingApiData:
    session = SessionLocal()
    suffix = uuid4().hex[:12]
    password = "Task3TestOnlyPassword!"
    users: dict[str, ApiUser] = {}
    orm_users: dict[str, User] = {}
    meetings: dict[str, int] = {}
    try:
        password_hash = hash_password(password)
        for name, role in (
            ("host", UserRole.USER),
            ("participant", UserRole.USER),
            ("shared", UserRole.USER),
            ("unrelated", UserRole.USER),
            ("admin", UserRole.ADMIN),
        ):
            username = f"p2t3_{name}_{suffix}"
            user = User(
                username=username,
                password_hash=password_hash,
                employee_no=f"P2T3-{name[:3]}-{suffix}",
                display_name=f"{name.title()} {suffix}",
                role=role.value,
            )
            session.add(user)
            session.flush()
            orm_users[name] = user
            users[name] = ApiUser(id=user.id, username=username, password=password)

        def add_meeting(
            name: str,
            *,
            creator_user_id: int | None,
            subject: str,
            meeting_code: str,
            start_time: datetime,
            meeting_status: MeetingStatus,
            minutes_status: MinutesStatus,
        ) -> Meeting:
            meeting = Meeting(
                tencent_meeting_id=f"p2t3_{name}_{suffix}",
                meeting_code=meeting_code,
                subject=subject,
                creator_user_id=creator_user_id,
                start_time=start_time,
                meeting_status=meeting_status.value,
                minutes_status=minutes_status.value,
            )
            session.add(meeting)
            session.flush()
            meetings[name] = meeting.id
            return meeting

        host_a = add_meeting(
            "host_a",
            creator_user_id=orm_users["host"].id,
            subject=f"Alpha Roadmap {suffix}",
            meeting_code=f"ALPHA-{suffix}",
            start_time=datetime(2026, 2, 3, 10, 0),
            meeting_status=MeetingStatus.ENDED,
            minutes_status=MinutesStatus.READY,
        )
        host_b = add_meeting(
            "host_b",
            creator_user_id=orm_users["host"].id,
            subject=f"Beta Review {suffix}",
            meeting_code=f"BETA-{suffix}",
            start_time=datetime(2026, 2, 3, 10, 0),
            meeting_status=MeetingStatus.ENDED,
            minutes_status=MinutesStatus.READY,
        )
        joined = add_meeting(
            "joined",
            creator_user_id=orm_users["unrelated"].id,
            subject=f"Joined Discussion {suffix}",
            meeting_code=f"JOINED-{suffix}",
            start_time=datetime(2026, 2, 2, 11, 0),
            meeting_status=MeetingStatus.SCHEDULED,
            minutes_status=MinutesStatus.DISABLED,
        )
        shared = add_meeting(
            "shared",
            creator_user_id=orm_users["unrelated"].id,
            subject=f"Shared Planning {suffix}",
            meeting_code=f"SHARE-CODE-{suffix}",
            start_time=datetime(2026, 2, 2, 10, 0),
            meeting_status=MeetingStatus.ENDED,
            minutes_status=MinutesStatus.WAITING_TRANSCRIPT,
        )
        nullable_host = add_meeting(
            "nullable_host",
            creator_user_id=None,
            subject=f"External Host Meeting {suffix}",
            meeting_code=f"EXTERNAL-{suffix}",
            start_time=datetime(2026, 2, 1, 10, 0),
            meeting_status=MeetingStatus.ENDED,
            minutes_status=MinutesStatus.READY,
        )
        add_meeting(
            "other",
            creator_user_id=orm_users["unrelated"].id,
            subject=f"Other Meeting {suffix}",
            meeting_code=f"OTHER-{suffix}",
            start_time=datetime(2026, 1, 31, 10, 0),
            meeting_status=MeetingStatus.ENDED,
            minutes_status=MinutesStatus.FAILED,
        )

        session.add_all(
            [
                MeetingParticipant(
                    meeting_id=host_a.id,
                    user_id=orm_users["host"].id,
                    display_name=orm_users["host"].display_name,
                    is_internal=True,
                ),
                MeetingParticipant(
                    meeting_id=joined.id,
                    user_id=orm_users["participant"].id,
                    display_name=orm_users["participant"].display_name,
                    is_internal=True,
                ),
                # Duplicate participant rows are valid in the current schema; EXISTS must deduplicate the list.
                MeetingParticipant(
                    meeting_id=joined.id,
                    user_id=orm_users["participant"].id,
                    display_name=orm_users["participant"].display_name,
                    is_internal=True,
                ),
                MeetingParticipant(
                    meeting_id=host_a.id,
                    user_id=None,
                    tencent_userid=f"external_host_a_{suffix}",
                    display_name="External Customer",
                    is_internal=False,
                ),
                MeetingParticipant(
                    meeting_id=nullable_host.id,
                    user_id=None,
                    tencent_userid=f"external_nullable_{suffix}",
                    display_name="External Host",
                    is_internal=False,
                ),
            ]
        )
        session.add_all(
            [
                MeetingPermission(
                    meeting_id=host_a.id,
                    user_id=orm_users["host"].id,
                    permission=MeetingPermissionType.VIEW.value,
                    granted_by=orm_users["host"].id,
                ),
                MeetingPermission(
                    meeting_id=joined.id,
                    user_id=orm_users["participant"].id,
                    permission=MeetingPermissionType.VIEW.value,
                    granted_by=orm_users["unrelated"].id,
                ),
                MeetingPermission(
                    meeting_id=shared.id,
                    user_id=orm_users["shared"].id,
                    permission=MeetingPermissionType.VIEW.value,
                    granted_by=orm_users["unrelated"].id,
                ),
                MeetingPermission(
                    meeting_id=nullable_host.id,
                    user_id=orm_users["shared"].id,
                    permission=MeetingPermissionType.VIEW.value,
                    granted_by=orm_users["unrelated"].id,
                ),
            ]
        )
        session.commit()

        yield MeetingApiData(
            session=session,
            users=users,
            orm_users=orm_users,
            meetings=meetings,
            meeting_ids=list(meetings.values()),
            user_ids=[user.id for user in orm_users.values()],
        )
    finally:
        session.rollback()
        if meetings:
            session.execute(delete(Meeting).where(Meeting.id.in_(meetings.values())))
            session.commit()
        if orm_users:
            session.execute(delete(User).where(User.id.in_([user.id for user in orm_users.values()])))
            session.commit()
        session.close()
        redis_client = Redis.from_url(get_settings().redis_url, decode_responses=True)
        try:
            user_ids = {user.id for user in orm_users.values()}
            for key in redis_client.scan_iter(match="aimm:auth:refresh:*"):
                try:
                    value = json.loads(redis_client.get(key) or "{}")
                except ValueError:
                    value = {}
                if value.get("user_id") in user_ids:
                    redis_client.delete(key)
        finally:
            redis_client.close()


def _access_token(client: TestClient, user: ApiUser) -> str:
    response = client.post("/api/v1/auth/login", json={"username": user.username, "password": user.password})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user"]["id"] == user.id
    return data["access_token"]


def _headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_real_jwt_meeting_list_scopes_filters_pagination_and_roles(meeting_api_data: MeetingApiData) -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/meetings").status_code == 401
        host_token = _access_token(client, meeting_api_data.users["host"])
        participant_token = _access_token(client, meeting_api_data.users["participant"])
        shared_token = _access_token(client, meeting_api_data.users["shared"])
        unrelated_token = _access_token(client, meeting_api_data.users["unrelated"])
        admin_token = _access_token(client, meeting_api_data.users["admin"])

        hosted = client.get(
            "/api/v1/meetings",
            headers={**_headers(host_token), "X-Request-ID": "req_task3_list"},
        )
        assert hosted.status_code == 200
        assert hosted.headers["X-Request-ID"] == "req_task3_list"
        hosted_body = hosted.json()
        assert hosted_body["request_id"] == "req_task3_list"
        assert [item["id"] for item in hosted_body["data"]["items"]] == [
            meeting_api_data.meetings["host_b"],
            meeting_api_data.meetings["host_a"],
        ]
        assert {item["my_role"] for item in hosted_body["data"]["items"]} == {MeetingRelation.HOST.value}
        assert hosted_body["data"]["page"] == 1
        assert hosted_body["data"]["total"] == 2
        assert hosted_body["data"]["total_pages"] == 1

        joined = client.get("/api/v1/meetings?scope=joined", headers=_headers(participant_token))
        assert joined.status_code == 200
        assert [item["id"] for item in joined.json()["data"]["items"]] == [meeting_api_data.meetings["joined"]]
        assert joined.json()["data"]["items"][0]["my_role"] == MeetingRelation.PARTICIPANT.value

        shared = client.get("/api/v1/meetings?scope=shared", headers=_headers(shared_token))
        assert shared.status_code == 200
        assert [item["id"] for item in shared.json()["data"]["items"]] == [
            meeting_api_data.meetings["shared"],
            meeting_api_data.meetings["nullable_host"],
        ]
        assert {item["my_role"] for item in shared.json()["data"]["items"]} == {MeetingRelation.SHARED.value}

        forbidden_all = client.get("/api/v1/meetings?scope=all", headers=_headers(unrelated_token))
        assert forbidden_all.status_code == 403
        assert forbidden_all.json()["code"] == PERMISSION_ADMIN_REQUIRED

        admin_all = client.get("/api/v1/meetings?scope=all", headers=_headers(admin_token))
        assert admin_all.status_code == 200
        assert admin_all.json()["data"]["total"] == 6
        assert {item["my_role"] for item in admin_all.json()["data"]["items"]} == {MeetingRelation.ADMIN.value}

        by_status = client.get(
            "/api/v1/meetings?meeting_status=ENDED&minutes_status=READY",
            headers=_headers(host_token),
        )
        assert [item["id"] for item in by_status.json()["data"]["items"]] == [
            meeting_api_data.meetings["host_b"],
            meeting_api_data.meetings["host_a"],
        ]
        by_subject = client.get("/api/v1/meetings?keyword=Alpha%20Roadmap", headers=_headers(host_token))
        assert [item["id"] for item in by_subject.json()["data"]["items"]] == [meeting_api_data.meetings["host_a"]]
        by_code = client.get("/api/v1/meetings?keyword=BETA-", headers=_headers(host_token))
        assert [item["id"] for item in by_code.json()["data"]["items"]] == [meeting_api_data.meetings["host_b"]]

        first_page = client.get("/api/v1/meetings?page=1&page_size=1", headers=_headers(host_token))
        second_page = client.get("/api/v1/meetings?page=2&page_size=1", headers=_headers(host_token))
        assert first_page.json()["data"]["items"][0]["id"] == meeting_api_data.meetings["host_b"]
        assert first_page.json()["data"]["items"][0]["my_role"] == MeetingRelation.HOST.value
        assert {
            key: first_page.json()["data"][key]
            for key in ("page", "page_size", "total", "total_pages")
        } == {"page": 1, "page_size": 1, "total": 2, "total_pages": 2}
        assert second_page.json()["data"]["items"][0]["id"] == meeting_api_data.meetings["host_a"]

        empty = client.get("/api/v1/meetings?scope=shared&keyword=not-found", headers=_headers(shared_token))
        assert empty.status_code == 200
        assert empty.json()["data"] == {"items": [], "page": 1, "page_size": 20, "total": 0, "total_pages": 0}
        for invalid in ("/api/v1/meetings?page=0", "/api/v1/meetings?page_size=101"):
            response = client.get(invalid, headers=_headers(host_token))
            assert response.status_code == 422
            assert response.json()["code"] == 90001


def test_real_jwt_meeting_detail_permissions_errors_and_nullable_fields(meeting_api_data: MeetingApiData) -> None:
    with TestClient(app) as client:
        host_token = _access_token(client, meeting_api_data.users["host"])
        participant_token = _access_token(client, meeting_api_data.users["participant"])
        shared_token = _access_token(client, meeting_api_data.users["shared"])
        unrelated_token = _access_token(client, meeting_api_data.users["unrelated"])
        admin_token = _access_token(client, meeting_api_data.users["admin"])

        assert client.get(f"/api/v1/meetings/{meeting_api_data.meetings['host_a']}").status_code == 401
        host = client.get(f"/api/v1/meetings/{meeting_api_data.meetings['host_a']}", headers=_headers(host_token))
        assert host.status_code == 200
        host_data = host.json()["data"]
        assert host_data["host"]["id"] == meeting_api_data.users["host"].id
        assert host_data["permissions"] == {
            "can_view": True,
            "can_edit_minutes": True,
            "can_regenerate": True,
            "can_manage_permissions": True,
            "can_view_ai_versions": True,
        }
        assert {participant["user_id"] for participant in host_data["participants"]} == {
            meeting_api_data.users["host"].id,
            None,
        }

        participant = client.get(
            f"/api/v1/meetings/{meeting_api_data.meetings['joined']}", headers=_headers(participant_token)
        )
        assert participant.status_code == 200
        assert participant.json()["data"]["permissions"] == {
            "can_view": True,
            "can_edit_minutes": False,
            "can_regenerate": False,
            "can_manage_permissions": False,
            "can_view_ai_versions": False,
        }

        shared = client.get(
            f"/api/v1/meetings/{meeting_api_data.meetings['shared']}", headers=_headers(shared_token)
        )
        assert shared.status_code == 200
        assert shared.json()["data"]["permissions"]["can_edit_minutes"] is False

        nullable = client.get(
            f"/api/v1/meetings/{meeting_api_data.meetings['nullable_host']}", headers=_headers(shared_token)
        )
        assert nullable.status_code == 200
        assert nullable.json()["data"]["host"] is None
        assert nullable.json()["data"]["participants"] == [
            {"user_id": None, "display_name": "External Host", "is_internal": False}
        ]

        admin = client.get(f"/api/v1/meetings/{meeting_api_data.meetings['host_a']}", headers=_headers(admin_token))
        assert admin.status_code == 200
        assert all(admin.json()["data"]["permissions"].values())

        unrelated = client.get(
            f"/api/v1/meetings/{meeting_api_data.meetings['host_a']}", headers=_headers(unrelated_token)
        )
        assert unrelated.status_code == 403
        assert unrelated.json()["code"] == PERMISSION_MEETING_ACCESS_DENIED

        missing = client.get("/api/v1/meetings/99999999", headers=_headers(host_token))
        assert missing.status_code == 404
        assert missing.json()["code"] == MEETING_NOT_FOUND


def test_meeting_service_uses_one_batch_query_per_relation_type(meeting_api_data: MeetingApiData) -> None:
    session = meeting_api_data.session
    participant_repository = ParticipantRepository(session)
    permission_repository = PermissionRepository(session)
    service = MeetingService(
        meeting_repository=MeetingRepository(session),
        participant_repository=participant_repository,
        permission_repository=permission_repository,
        permission_service=PermissionService(participant_repository, permission_repository),
    )
    statements: list[str] = []

    def capture_statement(*args: object) -> None:
        statements.append(str(args[2]))

    event.listen(engine, "before_cursor_execute", capture_statement)
    try:
        result = service.list_meetings(current_user=meeting_api_data.orm_users["host"])
    finally:
        event.remove(engine, "before_cursor_execute", capture_statement)

    assert [item.id for item in result.items] == [
        meeting_api_data.meetings["host_b"],
        meeting_api_data.meetings["host_a"],
    ]
    assert {item.my_role for item in result.items} == {MeetingRelation.HOST}
    assert sum("meeting_participants" in statement for statement in statements) == 1
    assert sum("meeting_permissions" in statement for statement in statements) == 1

    with pytest.raises(AppException) as exc_info:
        service.list_meetings(current_user=meeting_api_data.orm_users["host"], scope=MeetingScope.ALL)
    assert exc_info.value.code == PERMISSION_ADMIN_REQUIRED
