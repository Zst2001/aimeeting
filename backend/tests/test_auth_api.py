import json
from dataclasses import dataclass
from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from redis import Redis

from app.api.dependencies import ensure_admin
from app.core.config import get_settings
from app.core.error_codes import (
    AUTH_INVALID_CREDENTIALS,
    AUTH_REFRESH_TOKEN_INVALID,
    AUTH_TOKEN_EXPIRED,
    AUTH_TOKEN_INVALID,
    AUTH_USER_DISABLED,
    PERMISSION_ADMIN_REQUIRED,
)
from app.core.exceptions import AppException
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.db.models.user import UserRole, UserStatus
from app.db.session import SessionLocal
from app.main import app
from app.repositories.user_repository import UserRepository
from app.services.refresh_session_service import refresh_session_key


@dataclass(frozen=True)
class AuthUser:
    id: int
    username: str
    password: str


@pytest.fixture
def auth_user() -> AuthUser:
    suffix = uuid4().hex[:12]
    username = f"auth_{suffix}"
    password = "CorrectHorseBatteryStaple!"
    from app.core.security import hash_password

    with SessionLocal() as session:
        user = UserRepository(session).create(
            username=username,
            password_hash=hash_password(password),
            display_name="Authentication Test User",
            employee_no=f"AUT{suffix}",
        )
        session.commit()
        auth_user_record = AuthUser(id=user.id, username=username, password=password)

    yield auth_user_record

    with SessionLocal() as session:
        user = UserRepository(session).get_by_id(auth_user_record.id)
        if user is not None:
            session.delete(user)
            session.commit()
    redis_client = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        for key in redis_client.scan_iter(match="aimm:auth:refresh:*"):
            raw_value = redis_client.get(key)
            try:
                value = json.loads(raw_value) if raw_value is not None else {}
            except ValueError:
                value = {}
            if value.get("user_id") == auth_user_record.id:
                redis_client.delete(key)
    finally:
        redis_client.close()


@pytest.fixture
def redis_client() -> Redis:
    client = Redis.from_url(get_settings().redis_url, decode_responses=True)
    assert client.ping()
    try:
        yield client
    finally:
        client.close()


def _login(client: TestClient, auth_user: AuthUser) -> dict[str, object]:
    response = client.post("/api/v1/auth/login", json={"username": auth_user.username, "password": auth_user.password})
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    return body["data"]


def test_login_me_refresh_rotation_logout_real_mysql_and_redis(auth_user: AuthUser, redis_client: Redis) -> None:
    with TestClient(app) as client:
        login_data = _login(client, auth_user)
        access_a = login_data["access_token"]
        refresh_a = login_data["refresh_token"]
        refresh_a_jti = decode_token(refresh_a)["jti"]

        assert login_data["token_type"] == "bearer"
        assert login_data["user"] == {
            "id": auth_user.id,
            "username": auth_user.username,
            "display_name": "Authentication Test User",
            "role": "USER",
        }
        assert redis_client.exists(refresh_session_key(refresh_a_jti))

        me_response = client.get("/api/v1/me", headers={"Authorization": f"Bearer {access_a}"})
        assert me_response.status_code == 200
        assert me_response.json()["data"]["id"] == auth_user.id
        assert "password_hash" not in me_response.text

        with SessionLocal() as session:
            user = UserRepository(session).get_by_id(auth_user.id)
            assert user is not None and user.last_login_at is not None

        refresh_response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_a})
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()["data"]
        refresh_b = refresh_data["refresh_token"]
        refresh_b_jti = decode_token(refresh_b)["jti"]
        assert not redis_client.exists(refresh_session_key(refresh_a_jti))
        assert redis_client.exists(refresh_session_key(refresh_b_jti))

        replay_response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_a})
        assert replay_response.status_code == 401
        assert replay_response.json()["code"] == AUTH_REFRESH_TOKEN_INVALID

        access_b = refresh_data["access_token"]
        assert client.get("/api/v1/me", headers={"Authorization": f"Bearer {access_b}"}).status_code == 200

        logout_response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_b},
            headers={"Authorization": f"Bearer {access_b}"},
        )
        assert logout_response.status_code == 204
        assert logout_response.content == b""
        assert not redis_client.exists(refresh_session_key(refresh_b_jti))

        repeated_logout = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_b},
            headers={"Authorization": f"Bearer {access_b}"},
        )
        assert repeated_logout.status_code == 204

        logged_out_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_b})
        assert logged_out_refresh.status_code == 401
        assert logged_out_refresh.json()["code"] == AUTH_REFRESH_TOKEN_INVALID


def test_login_invalid_credentials_and_disabled_user(auth_user: AuthUser) -> None:
    with TestClient(app) as client:
        wrong_password = client.post(
            "/api/v1/auth/login", json={"username": auth_user.username, "password": "WrongPassword123!"}
        )
        unknown_user = client.post(
            "/api/v1/auth/login", json={"username": "unknown_user", "password": "WrongPassword123!"}
        )
        for response in (wrong_password, unknown_user):
            assert response.status_code == 401
            assert response.json()["code"] == AUTH_INVALID_CREDENTIALS

        with SessionLocal() as session:
            user = UserRepository(session).get_by_id(auth_user.id)
            assert user is not None
            assert user.last_login_at is None
            user.status = UserStatus.DISABLED.value
            session.commit()

        disabled = client.post(
            "/api/v1/auth/login", json={"username": auth_user.username, "password": auth_user.password}
        )
        assert disabled.status_code == 403
        assert disabled.json()["code"] == AUTH_USER_DISABLED


def test_me_token_validation_and_disabled_user(auth_user: AuthUser) -> None:
    with TestClient(app) as client:
        login_data = _login(client, auth_user)
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]

        missing = client.get("/api/v1/me")
        invalid = client.get("/api/v1/me", headers={"Authorization": "Bearer invalid-token"})
        wrong_type = client.get("/api/v1/me", headers={"Authorization": f"Bearer {refresh_token}"})
        expired_token = create_access_token(
            user_id=auth_user.id,
            username=auth_user.username,
            role="USER",
            expires_delta=timedelta(seconds=-1),
        )
        expired = client.get("/api/v1/me", headers={"Authorization": f"Bearer {expired_token}"})
        for response in (missing, invalid, wrong_type):
            assert response.status_code == 401
            assert response.json()["code"] == AUTH_TOKEN_INVALID
        assert expired.status_code == 401
        assert expired.json()["code"] == AUTH_TOKEN_EXPIRED

        with SessionLocal() as session:
            user = UserRepository(session).get_by_id(auth_user.id)
            assert user is not None
            user.status = UserStatus.DISABLED.value
            session.commit()
        disabled = client.get("/api/v1/me", headers={"Authorization": f"Bearer {access_token}"})
        assert disabled.status_code == 403
        assert disabled.json()["code"] == AUTH_USER_DISABLED


def test_refresh_rejects_wrong_type_expired_and_disabled_user(auth_user: AuthUser, redis_client: Redis) -> None:
    with TestClient(app) as client:
        login_data = _login(client, auth_user)
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]
        refresh_jti = decode_token(refresh_token)["jti"]

        wrong_type = client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
        expired_token = create_refresh_token(
            user_id=auth_user.id,
            username=auth_user.username,
            role="USER",
            expires_delta=timedelta(seconds=-1),
        )
        expired = client.post("/api/v1/auth/refresh", json={"refresh_token": expired_token})
        assert wrong_type.status_code == 401
        assert wrong_type.json()["code"] == AUTH_TOKEN_INVALID
        assert expired.status_code == 401
        assert expired.json()["code"] == AUTH_TOKEN_EXPIRED

        with SessionLocal() as session:
            user = UserRepository(session).get_by_id(auth_user.id)
            assert user is not None
            user.status = UserStatus.DISABLED.value
            session.commit()

        disabled = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert disabled.status_code == 403
        assert disabled.json()["code"] == AUTH_USER_DISABLED
        assert not redis_client.exists(refresh_session_key(refresh_jti))


def test_require_admin_allows_admin_and_rejects_user() -> None:
    from app.db.models.user import User

    assert ensure_admin(User(role=UserRole.ADMIN.value)).role == UserRole.ADMIN.value
    with pytest.raises(AppException) as exc_info:
        ensure_admin(User(role=UserRole.USER.value))
    assert exc_info.value.code == PERMISSION_ADMIN_REQUIRED
