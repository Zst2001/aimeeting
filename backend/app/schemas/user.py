from pydantic import BaseModel, ConfigDict

from app.db.models.user import User


class LoginUserResponse(BaseModel):
    id: int
    username: str
    display_name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class CurrentUserResponse(BaseModel):
    id: int
    username: str
    employee_no: str | None
    display_name: str
    email: str | None
    role: str
    status: str

    model_config = ConfigDict(from_attributes=True)


def login_user_response(user: User) -> LoginUserResponse:
    return LoginUserResponse.model_validate(user)


def current_user_response(user: User) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(user)
