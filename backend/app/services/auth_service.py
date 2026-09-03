from dataclasses import dataclass

from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app.core.error_codes import (
    AUTH_INVALID_CREDENTIALS,
    AUTH_REFRESH_TOKEN_INVALID,
    AUTH_TOKEN_EXPIRED,
    AUTH_TOKEN_INVALID,
    AUTH_USER_DISABLED,
    SYSTEM_INTERNAL_ERROR,
    SYSTEM_SERVICE_UNAVAILABLE,
)
from app.core.exceptions import AppException
from app.core.security import (
    TokenExpiredError,
    TokenInvalidError,
    create_access_token,
    create_refresh_token,
    decode_token,
    require_token_type,
    token_ttl_seconds,
    verify_password,
)
from app.db.models.user import User, UserStatus
from app.repositories.user_repository import UserRepository
from app.services.refresh_session_service import RefreshSessionService


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int


class AuthService:
    def __init__(self, user_repository: UserRepository, refresh_sessions: RefreshSessionService) -> None:
        self.user_repository = user_repository
        self.refresh_sessions = refresh_sessions

    def login(self, *, username: str, password: str) -> tuple[User, TokenPair]:
        user = self.user_repository.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            raise AppException("用户名或密码错误", AUTH_INVALID_CREDENTIALS, 401)
        self._ensure_active(user)

        tokens = self._issue_tokens(user)
        try:
            self.user_repository.update_last_login(user)
            self.user_repository.session.commit()
        except SQLAlchemyError as exc:
            self.user_repository.session.rollback()
            self._delete_refresh_session_safely(tokens.refresh_token)
            raise AppException("系统内部错误", SYSTEM_INTERNAL_ERROR, 500) from exc
        return user, tokens

    def refresh(self, *, refresh_token: str) -> TokenPair:
        payload = self._decode_refresh_token(refresh_token)
        jti = _string_claim(payload, "jti")
        subject_user_id = _user_id_claim(payload)

        try:
            session = self.refresh_sessions.consume(jti)
        except RedisError as exc:
            raise AppException("认证服务暂时不可用，请稍后重试", SYSTEM_SERVICE_UNAVAILABLE, 503) from exc
        if session is None or session.user_id != subject_user_id:
            raise AppException("Refresh Token 无效", AUTH_REFRESH_TOKEN_INVALID, 401)

        user = self.user_repository.get_by_id(subject_user_id)
        if user is None:
            raise AppException("Refresh Token 无效", AUTH_REFRESH_TOKEN_INVALID, 401)
        self._ensure_active(user)
        return self._issue_tokens(user)

    def logout(self, *, refresh_token: str, expected_user_id: int) -> None:
        payload = self._decode_refresh_token(refresh_token)
        if _user_id_claim(payload) != expected_user_id:
            raise AppException("Token 无效", AUTH_TOKEN_INVALID, 401)
        try:
            self.refresh_sessions.delete(_string_claim(payload, "jti"))
        except RedisError as exc:
            raise AppException("认证服务暂时不可用，请稍后重试", SYSTEM_SERVICE_UNAVAILABLE, 503) from exc

    def _issue_tokens(self, user: User) -> TokenPair:
        access_token = create_access_token(user_id=user.id, username=user.username, role=user.role)
        refresh_token = create_refresh_token(user_id=user.id, username=user.username, role=user.role)
        try:
            refresh_payload = self._decode_refresh_token(refresh_token)
            self.refresh_sessions.store(
                jti=_string_claim(refresh_payload, "jti"),
                user_id=user.id,
                ttl_seconds=token_ttl_seconds(refresh_payload),
            )
        except RedisError as exc:
            raise AppException("认证服务暂时不可用，请稍后重试", SYSTEM_SERVICE_UNAVAILABLE, 503) from exc
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=token_ttl_seconds(decode_token(access_token)),
        )

    def _decode_refresh_token(self, refresh_token: str) -> dict[str, object]:
        try:
            payload = decode_token(refresh_token)
            require_token_type(payload, "refresh")
            return payload
        except TokenExpiredError as exc:
            raise AppException("Token 已过期", AUTH_TOKEN_EXPIRED, 401) from exc
        except TokenInvalidError as exc:
            raise AppException("Token 无效", AUTH_TOKEN_INVALID, 401) from exc

    @staticmethod
    def _ensure_active(user: User) -> None:
        if user.status != UserStatus.ACTIVE.value:
            raise AppException("用户已禁用", AUTH_USER_DISABLED, 403)

    def _delete_refresh_session_safely(self, refresh_token: str) -> None:
        try:
            self.refresh_sessions.delete(_string_claim(self._decode_refresh_token(refresh_token), "jti"))
        except (AppException, RedisError):
            pass


def _string_claim(payload: dict[str, object], name: str) -> str:
    value = payload.get(name)
    if not isinstance(value, str):
        raise AppException("Token 无效", AUTH_TOKEN_INVALID, 401)
    return value


def _user_id_claim(payload: dict[str, object]) -> int:
    subject = _string_claim(payload, "sub")
    try:
        user_id = int(subject)
    except ValueError as exc:
        raise AppException("Token 无效", AUTH_TOKEN_INVALID, 401) from exc
    if user_id <= 0:
        raise AppException("Token 无效", AUTH_TOKEN_INVALID, 401)
    return user_id
