from fastapi.testclient import TestClient

from app.main import app


def test_health_reports_application_availability() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_http_errors_use_problem_details() -> None:
    with TestClient(app) as client:
        response = client.get("/not-a-route")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["status"] == 404


def test_readiness_checks_database_connection() -> None:
    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
