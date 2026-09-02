from uuid import uuid4

from app.core.security import verify_password
from app.db.models.user import UserRole, UserStatus
from app.db.session import SessionLocal
from app.repositories.user_repository import UserRepository
from app.scripts import create_admin


def test_create_admin_creates_admin_and_does_not_overwrite_duplicate(monkeypatch) -> None:
    suffix = uuid4().hex[:12]
    username = f"admin_{suffix}"
    employee_no = f"A{suffix}"
    values = iter([username, "CLI Test Admin", employee_no, "", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(values))
    monkeypatch.setattr(create_admin, "getpass", lambda _: "AdminPassword123!")

    assert create_admin.main() == 0

    with SessionLocal() as session:
        repository = UserRepository(session)
        admin = repository.get_by_username(username)
        assert admin is not None
        assert admin.role == UserRole.ADMIN.value
        assert admin.status == UserStatus.ACTIVE.value
        assert admin.password_hash != "AdminPassword123!"
        assert verify_password("AdminPassword123!", admin.password_hash)

    duplicate_values = iter([username])
    monkeypatch.setattr("builtins.input", lambda _: next(duplicate_values))
    assert create_admin.main() == 1

    employee_no_conflict_values = iter([f"other_{suffix}", "Other Admin", employee_no])
    monkeypatch.setattr("builtins.input", lambda _: next(employee_no_conflict_values))
    assert create_admin.main() == 1

    with SessionLocal() as session:
        admin = UserRepository(session).get_by_username(username)
        assert admin is not None
        session.delete(admin)
        session.commit()
