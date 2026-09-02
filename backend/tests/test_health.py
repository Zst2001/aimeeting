from fastapi.testclient import TestClient

from app.api import health
from app.main import app


def test_health_returns_ok_and_request_id() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"].startswith("req_")


def test_health_preserves_client_request_id() -> None:
    with TestClient(app) as client:
        response = client.get("/health", headers={"X-Request-ID": "req_test_123"})

    assert response.headers["X-Request-ID"] == "req_test_123"


def test_ready_returns_ready_when_all_components_are_available(monkeypatch) -> None:
    monkeypatch.setattr(health, "check_mysql", lambda: None)
    monkeypatch.setattr(health, "check_redis", lambda: None)

    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "components": {"mysql": "ok", "redis": "ok"},
    }


def test_ready_returns_not_ready_when_a_component_fails(monkeypatch) -> None:
    def unavailable_mysql() -> None:
        raise ConnectionError("database unavailable")

    monkeypatch.setattr(health, "check_mysql", unavailable_mysql)
    monkeypatch.setattr(health, "check_redis", lambda: None)

    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "components": {"mysql": "error", "redis": "ok"},
    }
