from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.config import get_settings


_password_hasher = PasswordHasher(type=Type.ID)


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (InvalidHashError, VerificationError):
        return False


class TokenInvalidError(ValueError):
    """Raised when a JWT is malformed, forged, or has invalid required claims."""


class TokenExpiredError(TokenInvalidError):
    """Raised when a JWT expiration time has passed."""


def create_access_token(
    *,
    user_id: int,
    username: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    return _create_token(
        user_id=user_id,
        username=username,
        role=role,
        token_type="access",
        expires_delta=expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )


def create_refresh_token(
    *,
    user_id: int,
    username: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    return _create_token(
        user_id=user_id,
        username=username,
        role=role,
        token_type="refresh",
        expires_delta=expires_delta or timedelta(days=settings.jwt_refresh_token_expire_days),
    )


def decode_token(token: str) -> dict[str, object]:
    """Verify a token's signature and standard claims without accepting its use type."""

    settings = get_settings()
    if not settings.jwt_secret_key:
        raise TokenInvalidError("JWT secret is not configured")

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except ExpiredSignatureError as exc:
        raise TokenExpiredError("Token expired") from exc
    except InvalidTokenError as exc:
        raise TokenInvalidError("Invalid token") from exc

    required_claims = ("sub", "username", "role", "type", "jti", "iat", "exp")
    if any(claim not in payload for claim in required_claims):
        raise TokenInvalidError("Missing required token claims")
    if not isinstance(payload["sub"], str) or not payload["sub"].isdigit():
        raise TokenInvalidError("Invalid subject claim")
    if not all(isinstance(payload[claim], str) and payload[claim] for claim in ("username", "role", "type", "jti")):
        raise TokenInvalidError("Invalid token claims")
    if payload["type"] not in {"access", "refresh"}:
        raise TokenInvalidError("Invalid token type")
    return payload


def require_token_type(payload: dict[str, object], expected_type: str) -> None:
    if payload.get("type") != expected_type:
        raise TokenInvalidError("Unexpected token type")


def token_ttl_seconds(payload: dict[str, object]) -> int:
    exp = payload.get("exp")
    if not isinstance(exp, int):
        raise TokenInvalidError("Invalid expiration claim")
    return max(exp - int(datetime.now(timezone.utc).timestamp()), 1)


def _create_token(
    *,
    user_id: int,
    username: str,
    role: str,
    token_type: str,
    expires_delta: timedelta,
) -> str:
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise TokenInvalidError("JWT secret is not configured")

    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "type": token_type,
        "jti": uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
