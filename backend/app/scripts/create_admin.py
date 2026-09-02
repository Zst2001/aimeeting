from getpass import getpass

from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.db.models.user import UserRole, UserStatus
from app.db.session import SessionLocal
from app.repositories.user_repository import UserRepository


def _optional_input(prompt: str) -> str | None:
    return input(prompt).strip() or None


def main() -> int:
    username = input("Username: ").strip()
    if not username:
        print("Username is required.")
        return 1

    with SessionLocal() as session:
        repository = UserRepository(session)
        if repository.get_by_username(username) is not None:
            print(f"User '{username}' already exists.")
            return 1

        display_name = input("Display name: ").strip()
        if not display_name:
            print("Display name is required.")
            return 1

        employee_no = _optional_input("Employee no (optional): ")
        if employee_no and repository.get_by_employee_no(employee_no) is not None:
            print(f"Employee no '{employee_no}' already exists.")
            return 1

        email = _optional_input("Email (optional): ")
        tencent_userid = _optional_input("Tencent userid (optional): ")
        password = getpass("Password: ")
        password_confirmation = getpass("Confirm password: ")

        if not password:
            print("Password is required.")
            return 1
        if len(password) < 8:
            print("Password must be at least 8 characters.")
            return 1
        if password != password_confirmation:
            print("Passwords do not match.")
            return 1

        try:
            repository.create(
                username=username,
                password_hash=hash_password(password),
                display_name=display_name,
                employee_no=employee_no,
                email=email,
                tencent_userid=tencent_userid,
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
            )
            session.commit()
        except IntegrityError:
            session.rollback()
            print("User could not be created because username or employee no already exists.")
            return 1

    print("Admin user created successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
