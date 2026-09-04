from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, configure_mappers

from app.db.models import (
    Meeting,
    MeetingParticipant,
    MeetingPermission,
    MeetingPermissionType,
    MeetingStatus,
    MinutesStatus,
    User,
)
from app.db.session import SessionLocal, engine


@pytest.fixture(autouse=True)
def require_real_mysql() -> None:
    """Keep these domain constraints on the real MySQL integration path."""

    assert engine.dialect.name == "mysql"


def _suffix() -> str:
    return uuid4().hex[:12]


def _user(session: Session, suffix: str) -> User:
    user = User(
        username=f"meeting_{suffix}",
        password_hash="test-only-password-hash",
        employee_no=f"M{suffix}",
        display_name=f"Meeting Test {suffix}",
    )
    session.add(user)
    session.flush()
    return user


def _meeting(session: Session, suffix: str) -> Meeting:
    meeting = Meeting(tencent_meeting_id=f"tm_{suffix}", subject=f"Meeting {suffix}")
    session.add(meeting)
    session.flush()
    return meeting


def _cleanup(session: Session, meeting_ids: list[int], user_ids: list[int]) -> None:
    session.rollback()
    if meeting_ids:
        session.execute(delete(Meeting).where(Meeting.id.in_(meeting_ids)))
        session.flush()
    if user_ids:
        session.execute(delete(User).where(User.id.in_(user_ids)))
    session.commit()


def test_meeting_relationships_have_unambiguous_foreign_keys() -> None:
    configure_mappers()

    assert Meeting.creator.property.local_columns == {Meeting.__table__.c.creator_user_id}
    assert Meeting.ai_minutes_enabled_by_user.property.local_columns == {
        Meeting.__table__.c.ai_minutes_enabled_by
    }
    assert MeetingParticipant.user.property.local_columns == {MeetingParticipant.__table__.c.user_id}
    assert MeetingPermission.user.property.local_columns == {MeetingPermission.__table__.c.user_id}
    assert MeetingPermission.granted_by_user.property.local_columns == {MeetingPermission.__table__.c.granted_by}


def test_meeting_defaults_and_nullable_user_references_use_real_mysql() -> None:
    with SessionLocal() as session:
        meeting_ids: list[int] = []
        try:
            meeting = _meeting(session, _suffix())
            session.commit()
            meeting_ids.append(meeting.id)
            session.refresh(meeting)

            assert meeting.creator_user_id is None
            assert meeting.ai_minutes_enabled_by is None
            assert meeting.meeting_status == MeetingStatus.SCHEDULED.value
            assert meeting.ai_minutes_enabled is False
            assert meeting.minutes_status == MinutesStatus.DISABLED.value
            assert meeting.created_at is not None
            assert meeting.updated_at is not None
        finally:
            _cleanup(session, meeting_ids, [])


def test_tencent_meeting_id_is_unique_and_session_recovers_after_rollback() -> None:
    with SessionLocal() as session:
        meeting_ids: list[int] = []
        try:
            suffix = _suffix()
            meeting = _meeting(session, suffix)
            session.commit()
            meeting_ids.append(meeting.id)

            session.add(Meeting(tencent_meeting_id=meeting.tencent_meeting_id, subject="Duplicate"))
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()

            assert session.get(Meeting, meeting.id) is not None
        finally:
            _cleanup(session, meeting_ids, [])


def test_internal_and_external_participants_are_both_valid() -> None:
    with SessionLocal() as session:
        meeting_ids: list[int] = []
        user_ids: list[int] = []
        try:
            suffix = _suffix()
            user = _user(session, suffix)
            meeting = _meeting(session, suffix)
            internal = MeetingParticipant(
                meeting_id=meeting.id,
                user_id=user.id,
                display_name=user.display_name,
                is_internal=True,
            )
            external = MeetingParticipant(
                meeting_id=meeting.id,
                user_id=None,
                tencent_userid=f"external_{suffix}",
                display_name="External Participant",
                is_internal=False,
            )
            session.add_all([internal, external])
            session.commit()
            meeting_ids.append(meeting.id)
            user_ids.append(user.id)

            assert session.get(MeetingParticipant, internal.id).user_id == user.id  # type: ignore[union-attr]
            persisted_external = session.get(MeetingParticipant, external.id)
            assert persisted_external is not None
            assert persisted_external.user_id is None
            assert persisted_external.tencent_userid == f"external_{suffix}"
            assert persisted_external.is_internal is False
        finally:
            _cleanup(session, meeting_ids, user_ids)


def test_permission_default_unique_constraint_and_rollback_recovery() -> None:
    with SessionLocal() as session:
        meeting_ids: list[int] = []
        user_ids: list[int] = []
        try:
            suffix = _suffix()
            recipient = _user(session, f"recipient_{suffix}")
            grantor = _user(session, f"grantor_{suffix}")
            meeting = _meeting(session, suffix)
            permission = MeetingPermission(meeting_id=meeting.id, user_id=recipient.id, granted_by=grantor.id)
            session.add(permission)
            session.commit()
            meeting_ids.append(meeting.id)
            user_ids.extend([recipient.id, grantor.id])

            assert permission.permission == MeetingPermissionType.VIEW.value
            session.add(
                MeetingPermission(
                    meeting_id=meeting.id,
                    user_id=recipient.id,
                    permission=MeetingPermissionType.VIEW.value,
                    granted_by=grantor.id,
                )
            )
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()

            assert session.get(MeetingPermission, permission.id) is not None
        finally:
            _cleanup(session, meeting_ids, user_ids)


def test_participant_and_permission_foreign_keys_reject_missing_records() -> None:
    with SessionLocal() as session:
        meeting_ids: list[int] = []
        user_ids: list[int] = []
        try:
            suffix = _suffix()
            user = _user(session, suffix)
            meeting = _meeting(session, suffix)
            session.commit()
            meeting_ids.append(meeting.id)
            user_ids.append(user.id)

            session.add(MeetingParticipant(meeting_id=9_999_999_999, display_name="Missing Meeting"))
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()

            session.add(MeetingPermission(meeting_id=9_999_999_999, user_id=user.id, granted_by=user.id))
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()

            session.add(MeetingPermission(meeting_id=meeting.id, user_id=9_999_999_998, granted_by=user.id))
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()

            session.add(MeetingPermission(meeting_id=meeting.id, user_id=user.id, granted_by=9_999_999_997))
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()
        finally:
            _cleanup(session, meeting_ids, user_ids)


def test_deleting_meeting_cascades_participants_and_permissions_in_mysql() -> None:
    with SessionLocal() as session:
        user_ids: list[int] = []
        try:
            suffix = _suffix()
            user = _user(session, suffix)
            meeting = _meeting(session, suffix)
            participant = MeetingParticipant(
                meeting_id=meeting.id,
                user_id=user.id,
                display_name=user.display_name,
                is_internal=True,
            )
            permission = MeetingPermission(meeting_id=meeting.id, user_id=user.id, granted_by=user.id)
            session.add_all([participant, permission])
            session.commit()
            user_ids.append(user.id)
            participant_id = participant.id
            permission_id = permission.id

            session.execute(delete(Meeting).where(Meeting.id == meeting.id))
            session.commit()

            assert session.get(MeetingParticipant, participant_id) is None
            assert session.get(MeetingPermission, permission_id) is None
        finally:
            _cleanup(session, [], user_ids)
