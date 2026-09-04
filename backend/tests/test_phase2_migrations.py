from uuid import uuid4

from sqlalchemy import text

from app.db.session import SessionLocal, engine
from app.utils.datetime import utc_now


def test_phase2_server_defaults_are_created_by_real_mysql_migrations() -> None:
    """Exercise defaults written by 0002/0003 without ORM-side defaults."""

    assert engine.dialect.name == "mysql"
    suffix = uuid4().hex[:12]

    with SessionLocal() as session:
        meeting_id: int | None = None
        user_id: int | None = None
        try:
            now = utc_now()
            user_id = session.execute(
                text(
                    """
                    INSERT INTO users (username, password_hash, employee_no, display_name, role, status, created_at, updated_at)
                    VALUES (:username, :password_hash, :employee_no, :display_name, 'USER', 'ACTIVE', :now, :now)
                    """
                ),
                {
                    "username": f"migration_{suffix}",
                    "password_hash": "test-only-password-hash",
                    "employee_no": f"MG{suffix}",
                    "display_name": "Migration Test User",
                    "now": now,
                },
            ).lastrowid
            meeting_id = session.execute(
                text(
                    """
                    INSERT INTO meetings (tencent_meeting_id, subject, created_at, updated_at)
                    VALUES (:tencent_meeting_id, :subject, :now, :now)
                    """
                ),
                {"tencent_meeting_id": f"migration_tm_{suffix}", "subject": "Migration Defaults", "now": now},
            ).lastrowid
            session.execute(
                text(
                    """
                    INSERT INTO meeting_participants (meeting_id, display_name, created_at)
                    VALUES (:meeting_id, :display_name, :now)
                    """
                ),
                {"meeting_id": meeting_id, "display_name": "External Participant", "now": now},
            )
            session.execute(
                text(
                    """
                    INSERT INTO meeting_permissions (meeting_id, user_id, granted_by, created_at)
                    VALUES (:meeting_id, :user_id, :granted_by, :now)
                    """
                ),
                {"meeting_id": meeting_id, "user_id": user_id, "granted_by": user_id, "now": now},
            )
            session.commit()

            meeting = session.execute(
                text(
                    """
                    SELECT meeting_status, ai_minutes_enabled, minutes_status
                    FROM meetings
                    WHERE id = :meeting_id
                    """
                ),
                {"meeting_id": meeting_id},
            ).one()
            participant = session.execute(
                text("SELECT user_id, is_internal FROM meeting_participants WHERE meeting_id = :meeting_id"),
                {"meeting_id": meeting_id},
            ).one()
            permission = session.execute(
                text("SELECT permission FROM meeting_permissions WHERE meeting_id = :meeting_id"),
                {"meeting_id": meeting_id},
            ).one()

            assert meeting == ("SCHEDULED", 0, "DISABLED")
            assert participant == (None, 0)
            assert permission == ("VIEW",)
        finally:
            session.rollback()
            if meeting_id is not None:
                session.execute(text("DELETE FROM meetings WHERE id = :meeting_id"), {"meeting_id": meeting_id})
            if user_id is not None:
                session.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})
            session.commit()
