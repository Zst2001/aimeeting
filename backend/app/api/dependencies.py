from collections.abc import Generator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.error_codes import (
    AUTH_TOKEN_EXPIRED,
    AUTH_TOKEN_INVALID,
    AUTH_USER_DISABLED,
    PERMISSION_ADMIN_REQUIRED,
    SYSTEM_SERVICE_UNAVAILABLE,
)
from app.core.exceptions import AppException
from app.core.security import TokenExpiredError, TokenInvalidError, decode_token, require_token_type
from app.db.models.user import User, UserRole, UserStatus
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.participant_repository import ParticipantRepository
from app.repositories.permission_repository import PermissionRepository
from app.services.auth_service import AuthService
from app.services.meeting_service import MeetingService
from app.services.permission_service import PermissionService
from app.services.refresh_session_service import RefreshSessionService


bearer_scheme = HTTPBearer(auto_error=False)


def get_refresh_session_service() -> Generator[RefreshSessionService, None, None]:
    redis_client = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        yield RefreshSessionService(redis_client)
    finally:
        redis_client.close()


def get_auth_service(
    db: Session = Depends(get_db),
    refresh_sessions: RefreshSessionService = Depends(get_refresh_session_service),
) -> AuthService:
    return AuthService(UserRepository(db), refresh_sessions)


def get_meeting_service(db: Session = Depends(get_db)) -> MeetingService:
    participant_repository = ParticipantRepository(db)
    permission_repository = PermissionRepository(db)
    return MeetingService(
        meeting_repository=MeetingRepository(db),
        participant_repository=participant_repository,
        permission_repository=permission_repository,
        permission_service=PermissionService(participant_repository, permission_repository),
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppException("Token 无效", AUTH_TOKEN_INVALID, 401)
    try:
        payload = decode_token(credentials.credentials)
        require_token_type(payload, "access")
    except TokenExpiredError as exc:
        raise AppException("Token 已过期", AUTH_TOKEN_EXPIRED, 401) from exc
    except TokenInvalidError as exc:
        raise AppException("Token 无效", AUTH_TOKEN_INVALID, 401) from exc

    subject = payload.get("sub")
    try:
        user_id = int(subject) if isinstance(subject, str) else 0
    except ValueError as exc:
        raise AppException("Token 无效", AUTH_TOKEN_INVALID, 401) from exc
    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise AppException("Token 无效", AUTH_TOKEN_INVALID, 401)
    if user.status != UserStatus.ACTIVE.value:
        raise AppException("用户已禁用", AUTH_USER_DISABLED, 403)
    return user


def ensure_admin(user: User) -> User:
    if user.role != UserRole.ADMIN.value:
        raise AppException("需要管理员权限", PERMISSION_ADMIN_REQUIRED, 403)
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    return ensure_admin(current_user)
