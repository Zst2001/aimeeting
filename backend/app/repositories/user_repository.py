from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.user import User, UserRole, UserStatus


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        return self.session.scalar(select(User).where(User.username == username))

    def get_by_employee_no(self, employee_no: str) -> User | None:
        return self.session.scalar(select(User).where(User.employee_no == employee_no))

    def get_by_tencent_userid(self, tencent_userid: str) -> User | None:
        return self.session.scalar(select(User).where(User.tencent_userid == tencent_userid))

    def create(
        self,
        *,
        username: str,
        password_hash: str,
        display_name: str,
        employee_no: str | None = None,
        email: str | None = None,
        tencent_userid: str | None = None,
        role: UserRole = UserRole.USER,
        status: UserStatus = UserStatus.ACTIVE,
    ) -> User:
        user = User(
            username=username,
            password_hash=password_hash,
            display_name=display_name,
            employee_no=employee_no,
            email=email,
            tencent_userid=tencent_userid,
            role=role.value,
            status=status.value,
        )
        self.session.add(user)
        self.session.flush()
        return user
