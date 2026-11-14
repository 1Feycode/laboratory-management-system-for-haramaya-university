from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.models.user import User
from tests.conftest import insert_test_user


def login(client, email: str, password: str):
    return client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )


def test_password_hash_uses_bcrypt_cost_12_and_verifies() -> None:
    hashed = hash_password("SecurePass123")

    assert hashed.startswith("$2b$12$")
    assert hashed != "SecurePass123"
    assert verify_password("SecurePass123", hashed)
    assert not verify_password("WrongPass123", hashed)
    assert not verify_password("x" * 73, hashed)


def test_login_returns_access_token_and_httponly_refresh_cookie(
    client, test_engine
) -> None:
    user = insert_test_user(
        test_engine,
        email="admin@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )

    response = login(client, user.email, "SecurePass123")

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 1800
    assert body["user"]["role"] == "ULMD_ADMIN"
    assert "hashed_password" not in body["user"]
    assert response.cookies.get("RefreshToken")
    assert "httponly" in response.headers["set-cookie"].lower()


def test_invalid_credentials_and_fifth_attempt_lock_account(
    client, test_engine
) -> None:
    user = insert_test_user(
        test_engine,
        email="manager@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )

    responses = [login(client, user.email, "WrongPass123") for _ in range(5)]

    assert all(response.status_code == 401 for response in responses)
    response = login(client, user.email, "SecurePass123")
    assert response.status_code == 401


def test_login_does_not_disclose_inactive_user(client, test_engine) -> None:
    user = insert_test_user(
        test_engine,
        email="inactive@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
        is_active=False,
    )

    response = login(client, user.email, "SecurePass123")
    missing_user = login(client, "missing@example.edu", "SecurePass123")

    assert response.status_code == missing_user.status_code == 401
    assert response.json() == missing_user.json()


def test_me_requires_valid_nonexpired_access_token(client, test_engine) -> None:
    user = insert_test_user(
        test_engine,
        email="admin@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )
    response = login(client, user.email, "SecurePass123")
    access_token = response.json()["access_token"]

    assert client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    ).status_code == 200
    expired = jwt.encode(
        {
            "sub": str(user.id),
            "iat": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),
            "exp": int((datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp()),
            "token_type": "access",
        },
        get_settings().secret_key.get_secret_value(),
        algorithm="HS256",
    )

    assert client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired}"},
    ).status_code == 401
    assert client.get("/api/v1/auth/me").status_code == 401


def test_refresh_rotates_token_and_rejects_reuse(client, test_engine) -> None:
    user = insert_test_user(
        test_engine,
        email="admin@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )
    initial = login(client, user.email, "SecurePass123")
    old_refresh = initial.cookies.get("RefreshToken")

    refreshed = client.post(
        "/api/v1/auth/refresh",
    )

    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"] != initial.json()["access_token"]
    assert refreshed.cookies.get("RefreshToken") != old_refresh
    client.cookies.set("RefreshToken", old_refresh, path="/api/v1/auth")
    reused = client.post("/api/v1/auth/refresh")
    assert reused.status_code == 401


def test_logout_revokes_refresh_cookie(client, test_engine) -> None:
    user = insert_test_user(
        test_engine,
        email="admin@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )
    initial = login(client, user.email, "SecurePass123")
    refresh = initial.cookies.get("RefreshToken")

    client.cookies.set("RefreshToken", refresh, path="/api/v1/auth")
    logged_out = client.post("/api/v1/auth/logout")

    assert logged_out.status_code == 204
    client.cookies.set("RefreshToken", refresh, path="/api/v1/auth")
    assert client.post("/api/v1/auth/refresh").status_code == 401


def test_login_rate_limit_returns_429(client, test_engine) -> None:
    user = insert_test_user(
        test_engine,
        email="rate@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )

    responses = [login(client, user.email, "WrongPass123") for _ in range(10)]
    limited = login(client, user.email, "WrongPass123")

    assert all(response.status_code == 401 for response in responses)
    assert limited.status_code == 429
    assert "retry-after" in limited.headers
