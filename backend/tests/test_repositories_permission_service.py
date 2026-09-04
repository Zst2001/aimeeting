from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import delete, inspect
from sqlalchemy.orm import Session

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
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.participant_repository import ParticipantRepository
from app.repositories.permission_repository import PermissionRepository
from app.services.permission_service import MeetingPermissionSnapshot, MeetingRelation, PermissionService


@dataclass
class RepositoryData:
    session: Session
    users: dict[str, User]
    meetings: dict[str, Meeting]
    external_participant_id: int
    meeting_ids: list[int]
    user_ids: list[int]


@pytest.fixture(autouse=True)
def require_real_mysql() -> None:
    assert engine.dialect.name == "mysql"


@pytest.fixture
def repository_data() -> RepositoryData:
    session = SessionLocal()
    suffix = uuid4().hex[:12]
    users: dict[str, User] = {}
    meetings: dict[str, Meeting] = {}
    try:
        for name, role in (
            ("host", UserRole.USER),
            ("participant", UserRole.USER),
            ("shared", UserRole.USER),
            ("unrelated", UserRole.USER),
            ("admin", UserRole.ADMIN),
        ):
            user = User(
                username=f"p2t2_{name}_{suffix}",
                password_hash="test-only-password-hash",
                employee_no=f"P2T2-{name[:3]}-{suffix}",
                display_name=f"{name.title()} {suffix}",
                role=role.value,
            )
            session.add(user)
            session.flush()
            users[name] = user

        def add_meeting(
            name: str,
            *,
            creator: User,
            subject: str,
            meeting_code: str,
            start_time: datetime,
            meeting_status: MeetingStatus,
            minutes_status: MinutesStatus,
        ) -> Meeting:
            meeting = Meeting(
                tencent_meeting_id=f"p2t2_{name}_{suffix}",
                meeting_code=meeting_code,
                subject=subject,
                creator_user_id=creator.id,
                start_time=start_time,
                meeting_status=meeting_status.value,
                minutes_status=minutes_status.value,
            )
            session.add(meeting)
            session.flush()
            meetings[name] = meeting
            return meeting

        meeting_a = add_meeting(
            "a",
            creator=users["host"],
            subject=f"Alpha Roadmap {suffix}",
            meeting_code=f"AIM-ALPHA-{suffix}",
            start_time=datetime(2026, 1, 3, 10, 0),
            meeting_status=MeetingStatus.ENDED,
            minutes_status=MinutesStatus.READY,
        )
        add_meeting(
            "b",
            creator=users["host"],
            subject=f"Beta Review {suffix}",
            meeting_code=f"BETA-{suffix}",
            start_time=datetime(2026, 1, 3, 10, 0),
            meeting_status=MeetingStatus.SCHEDULED,
            minutes_status=MinutesStatus.DISABLED,
        )
        add_meeting(
            "c",
            creator=users["unrelated"],
            subject=f"Gamma Operations {suffix}",
            meeting_code=f"GAMMA-CODE-{suffix}",
            start_time=datetime(2026, 1, 2, 10, 0),
            meeting_status=MeetingStatus.ENDED,
            minutes_status=MinutesStatus.WAITING_TRANSCRIPT,
        )
        add_meeting(
            "admin_host",
            creator=users["admin"],
            subject=f"Admin Hosted {suffix}",
            meeting_code=f"ADMIN-{suffix}",
            start_time=datetime(2026, 1, 1, 10, 0),
            meeting_status=MeetingStatus.SCHEDULED,
            minutes_status=MinutesStatus.DISABLED,
        )

        session.add_all(
            [
                MeetingParticipant(
                    meeting_id=meeting_a.id,
                    user_id=users["host"].id,
                    display_name=users["host"].display_name,
                    is_internal=True,
                ),
                MeetingParticipant(
                    meeting_id=meeting_a.id,
                    user_id=users["participant"].id,
                    display_name=users["participant"].display_name,
                    is_internal=True,
                ),
                # The schema intentionally does not enforce a meeting/user unique pair.
                # EXISTS in MeetingRepository must still return this meeting just once.
                MeetingParticipant(
                    meeting_id=meeting_a.id,
                    user_id=users["participant"].id,
                    display_name=users["participant"].display_name,
                    is_internal=True,
                ),
            ]
        )
        external = MeetingParticipant(
            meeting_id=meeting_a.id,
            user_id=None,
            tencent_userid=f"external_{suffix}",
            display_name="External participant",
            is_internal=False,
        )
        session.add(external)
        session.add_all(
            [
                MeetingPermission(
                    meeting_id=meeting_a.id,
                    user_id=users["host"].id,
                    permission=MeetingPermissionType.VIEW.value,
                    granted_by=users["host"].id,
                ),
                MeetingPermission(
                    meeting_id=meeting_a.id,
                    user_id=users["participant"].id,
                    permission=MeetingPermissionType.VIEW.value,
                    granted_by=users["host"].id,
                ),
                MeetingPermission(
                    meeting_id=meeting_a.id,
                    user_id=users["shared"].id,
                    permission=MeetingPermissionType.VIEW.value,
                    granted_by=users["host"].id,
                ),
            ]
        )
        session.commit()

        yield RepositoryData(
            session=session,
            users=users,
            meetings=meetings,
            external_participant_id=external.id,
            meeting_ids=[meeting.id for meeting in meetings.values()],
            user_ids=[user.id for user in users.values()],
        )
    finally:
        session.rollback()
        if meetings:
            session.execute(delete(Meeting).where(Meeting.id.in_([meeting.id for meeting in meetings.values()])))
            session.commit()
        if users:
            session.execute(delete(User).where(User.id.in_([user.id for user in users.values()])))
            session.commit()
        session.close()


def _ids(meetings: list[Meeting]) -> list[int]:
    return [meeting.id for meeting in meetings]


def _service(session: Session) -> PermissionService:
    return PermissionService(ParticipantRepository(session), PermissionRepository(session))


def _capabilities(service: PermissionService, meeting: Meeting, user: User) -> tuple[bool, bool, bool, bool, bool, bool]:
    return (
        service.can_view_meeting(meeting=meeting, user=user),
        service.can_toggle_ai_minutes(meeting=meeting, user=user),
        service.can_edit_minutes(meeting=meeting, user=user),
        service.can_regenerate_minutes(meeting=meeting, user=user),
        service.can_manage_permissions(meeting=meeting, user=user),
        service.can_view_ai_versions(meeting=meeting, user=user),
    )


def test_meeting_repository_getters_and_scopes_use_real_mysql(repository_data: RepositoryData) -> None:
    repository = MeetingRepository(repository_data.session)
    meeting_a = repository_data.meetings["a"]

    assert repository.get_by_id(meeting_a.id) is meeting_a
    assert repository.get_by_id(9_999_999) is None
    assert repository.get_by_tencent_meeting_id(meeting_a.tencent_meeting_id) is meeting_a
    assert repository.get_by_tencent_meeting_id("missing") is None

    hosted = repository.list_meetings(user_id=repository_data.users["host"].id, scope="hosted")
    assert _ids(hosted) == [repository_data.meetings["b"].id, meeting_a.id]
    assert all("creator" not in inspect(meeting).unloaded for meeting in hosted)

    joined = repository.list_meetings(user_id=repository_data.users["participant"].id, scope="joined")
    shared = repository.list_meetings(user_id=repository_data.users["shared"].id, scope="shared")
    all_meetings = repository.list_meetings(user_id=repository_data.users["unrelated"].id, scope="all")

    assert _ids(joined) == [meeting_a.id]
    assert _ids(shared) == [meeting_a.id]
    assert _ids(all_meetings) == [
        repository_data.meetings["b"].id,
        meeting_a.id,
        repository_data.meetings["c"].id,
        repository_data.meetings["admin_host"].id,
    ]
    assert repository.count_meetings(user_id=repository_data.users["host"].id, scope="hosted") == 2
    assert repository.count_meetings(user_id=repository_data.users["participant"].id, scope="joined") == 1
    assert repository.count_meetings(user_id=repository_data.users["shared"].id, scope="shared") == 1
    assert repository.count_meetings(user_id=repository_data.users["unrelated"].id, scope="all") == 4


def test_meeting_repository_filters_keyword_pagination_and_stable_order(repository_data: RepositoryData) -> None:
    repository = MeetingRepository(repository_data.session)
    user_id = repository_data.users["unrelated"].id
    meeting_a = repository_data.meetings["a"]
    meeting_b = repository_data.meetings["b"]
    meeting_c = repository_data.meetings["c"]

    assert _ids(
        repository.list_meetings(user_id=user_id, scope="all", meeting_status=MeetingStatus.ENDED)
    ) == [meeting_a.id, meeting_c.id]
    assert _ids(
        repository.list_meetings(user_id=user_id, scope="all", minutes_status=MinutesStatus.READY)
    ) == [meeting_a.id]
    assert _ids(repository.list_meetings(user_id=user_id, scope="all", keyword="Alpha Roadmap")) == [meeting_a.id]
    assert _ids(repository.list_meetings(user_id=user_id, scope="all", keyword="GAMMA-CODE")) == [meeting_c.id]
    assert _ids(repository.list_meetings(user_id=user_id, scope="all", offset=0, limit=2)) == [meeting_b.id, meeting_a.id]
    assert _ids(repository.list_meetings(user_id=user_id, scope="all", offset=1, limit=1)) == [meeting_a.id]
    assert repository.count_meetings(user_id=user_id, scope="all", keyword="GAMMA-CODE") == 1

    with pytest.raises(ValueError):
        repository.list_meetings(user_id=user_id, scope="unknown")
    with pytest.raises(ValueError):
        repository.list_meetings(user_id=user_id, scope="all", offset=-1)


def test_participant_repository_keeps_external_rows_from_becoming_internal_access(
    repository_data: RepositoryData,
) -> None:
    repository = ParticipantRepository(repository_data.session)
    meeting_a = repository_data.meetings["a"]

    assert repository.is_participant(meeting_a.id, repository_data.users["participant"].id) is True
    assert repository.is_participant(meeting_a.id, repository_data.users["unrelated"].id) is False
    participants = repository.list_by_meeting(meeting_a.id)
    external = next(participant for participant in participants if participant.id == repository_data.external_participant_id)
    assert external.user_id is None
    assert external.is_internal is False
    assert len(participants) == 4


def test_permission_repository_only_reports_matching_view_grants(repository_data: RepositoryData) -> None:
    repository = PermissionRepository(repository_data.session)
    meeting_a = repository_data.meetings["a"]
    shared = repository_data.users["shared"]
    unrelated = repository_data.users["unrelated"]

    assert repository.has_permission(meeting_a.id, shared.id, MeetingPermissionType.VIEW) is True
    assert repository.has_view_permission(meeting_a.id, shared.id) is True
    assert repository.has_view_permission(meeting_a.id, unrelated.id) is False
    assert repository.has_view_permission(repository_data.meetings["b"].id, shared.id) is False


def test_permission_matrix_and_snapshot_are_centralized(repository_data: RepositoryData) -> None:
    service = _service(repository_data.session)
    meeting_a = repository_data.meetings["a"]
    expected = {
        "host": (MeetingRelation.HOST, (True, True, True, True, True, True)),
        "participant": (MeetingRelation.PARTICIPANT, (True, False, False, False, False, False)),
        "shared": (MeetingRelation.SHARED, (True, False, False, False, False, False)),
        "unrelated": (MeetingRelation.NONE, (False, False, False, False, False, False)),
        "admin": (MeetingRelation.ADMIN, (True, True, True, True, True, True)),
    }

    for name, (relation, capabilities) in expected.items():
        user = repository_data.users[name]
        snapshot = service.get_permission_snapshot(meeting=meeting_a, user=user)
        assert isinstance(snapshot, MeetingPermissionSnapshot)
        assert service.resolve_meeting_relation(meeting=meeting_a, user=user) is relation
        assert _capabilities(service, meeting_a, user) == capabilities
        assert snapshot == MeetingPermissionSnapshot(
            can_view=capabilities[0],
            can_toggle_ai_minutes=capabilities[1],
            can_edit_minutes=capabilities[2],
            can_regenerate=capabilities[3],
            can_manage_permissions=capabilities[4],
            can_view_ai_versions=capabilities[5],
        )


def test_overlap_relation_precedence_and_repository_dedup(repository_data: RepositoryData) -> None:
    service = _service(repository_data.session)
    meeting_a = repository_data.meetings["a"]
    admin_host_meeting = repository_data.meetings["admin_host"]

    assert service.resolve_meeting_relation(meeting=meeting_a, user=repository_data.users["host"]) is MeetingRelation.HOST
    assert (
        service.resolve_meeting_relation(meeting=meeting_a, user=repository_data.users["participant"])
        is MeetingRelation.PARTICIPANT
    )
    assert service.resolve_meeting_relation(
        meeting=admin_host_meeting, user=repository_data.users["admin"]
    ) is MeetingRelation.HOST
    assert service.resolve_meeting_relation(meeting=meeting_a, user=repository_data.users["admin"]) is MeetingRelation.ADMIN

    joined = MeetingRepository(repository_data.session).list_meetings(
        user_id=repository_data.users["participant"].id,
        scope="joined",
    )
    assert _ids(joined) == [meeting_a.id]
