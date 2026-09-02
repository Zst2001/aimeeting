from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.db.models.user import UserRole, UserStatus
from app.db.session import SessionLocal
from app.repositories.user_repository import UserRepository


def test_user_repository_uses_real_mysql_and_rejects_duplicate_username() -> None:
    suffix = uuid4().hex[:12]
    username = f"user_{suffix}"
    employee_no = f"E{suffix}"

    with SessionLocal() as session:
        repository = UserRepository(session)
        user = repository.create(
            username=username,
            password_hash=hash_password("CorrectHorseBatteryStaple!"),
            display_name="Repository Test User",
            employee_no=employee_no,
            email=f"{username}@example.test",
            tencent_userid=f"tm_{suffix}",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        session.commit()

        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.last_login_at is None
        assert repository.get_by_id(user.id) is not None
        assert repository.get_by_username(username).id == user.id  # type: ignore[union-attr]
        assert repository.get_by_employee_no(employee_no).id == user.id  # type: ignore[union-attr]
        assert repository.get_by_tencent_userid(f"tm_{suffix}").id == user.id  # type: ignore[union-attr]

        with pytest.raises(IntegrityError):
            repository.create(
                username=username,
                password_hash=hash_password("AnotherSecurePassword!"),
                display_name="Duplicate User",
            )
        session.rollback()
        assert repository.get_by_username(username).id == user.id  # type: ignore[union-attr]

        session.delete(user)
        session.commit()
