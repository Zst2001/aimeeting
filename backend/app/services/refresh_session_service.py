import json
from dataclasses import dataclass

from redis import Redis


@dataclass(frozen=True)
class RefreshSession:
    user_id: int


def refresh_session_key(jti: str) -> str:
    return f"aimm:auth:refresh:{jti}"


class RefreshSessionService:
    """Own the Redis key format and atomic one-time refresh-token consumption."""

    def __init__(self, redis_client: Redis) -> None:
        self.redis_client = redis_client

    def store(self, *, jti: str, user_id: int, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            raise ValueError("Refresh session TTL must be positive")
        self.redis_client.set(
            refresh_session_key(jti),
            json.dumps({"user_id": user_id}),
            ex=ttl_seconds,
        )

    def consume(self, jti: str) -> RefreshSession | None:
        """Atomically remove and return a refresh session using Redis GETDEL."""

        raw_value = self.redis_client.getdel(refresh_session_key(jti))
        return _parse_session(raw_value)

    def delete(self, jti: str) -> None:
        self.redis_client.delete(refresh_session_key(jti))

    def exists(self, jti: str) -> bool:
        return bool(self.redis_client.exists(refresh_session_key(jti)))


def _parse_session(raw_value: str | bytes | None) -> RefreshSession | None:
    if raw_value is None:
        return None
    if isinstance(raw_value, bytes):
        raw_value = raw_value.decode("utf-8")
    try:
        data = json.loads(raw_value)
    except (TypeError, ValueError):
        return None
    user_id = data.get("user_id") if isinstance(data, dict) else None
    if not isinstance(user_id, int) or user_id <= 0:
        return None
    return RefreshSession(user_id=user_id)
