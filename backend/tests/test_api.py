from fastapi.testclient import TestClient

from app.main import app


def test_health_check_is_public() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_validates_password_policy() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/register", json={"email": "short@example.com", "password": "too-short"})
    assert response.status_code == 422

