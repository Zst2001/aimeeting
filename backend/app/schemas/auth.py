from pydantic import BaseModel, Field

from app.schemas.user import CurrentUserResponse, LoginUserResponse


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginData(TokenPairResponse):
    user: LoginUserResponse


class ApiSuccessLoginResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: LoginData
    request_id: str


class ApiSuccessRefreshResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: TokenPairResponse
    request_id: str


class ApiSuccessCurrentUserResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: CurrentUserResponse
    request_id: str
