from concurrent.futures import ThreadPoolExecutor
import json
from uuid import uuid4

from redis import Redis

from app.core.config import get_settings
from app.services.refresh_session_service import RefreshSessionService, refresh_session_key


def test_refresh_session_uses_real_redis_ttl_and_atomic_getdel() -> None:
    redis_client = Redis.from_url(get_settings().redis_url, decode_responses=True)
    service = RefreshSessionService(redis_client)
    jti = uuid4().hex
    try:
        service.store(jti=jti, user_id=123, ttl_seconds=60)
        assert service.exists(jti)
        assert 1 <= redis_client.ttl(refresh_session_key(jti)) <= 60
        assert json.loads(redis_client.get(refresh_session_key(jti))) == {"user_id": 123}

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: service.consume(jti), range(2)))

        assert sorted(result.user_id for result in results if result is not None) == [123]
        assert sum(result is None for result in results) == 1
        assert not service.exists(jti)
    finally:
        redis_client.delete(refresh_session_key(jti))
        redis_client.close()
