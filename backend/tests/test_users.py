import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.security import hash_password
from app.core.security import verify_password
from tests.conftest import insert_test_department, insert_test_user
from app.models.user import User


def authenticate(client, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_user_management_is_for_ulmd_admin_only(client, test_engine) -> None:
    user = insert_test_user(
        test_engine,
        email="auditor@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="AUDITOR",
    )

    assert client.get("/api/v1/users").status_code == 401
    response = client.get(
        "/api/v1/users",
        headers=authenticate(client, user.email, "SecurePass123"),
    )
    assert response.status_code == 403


def test_admin_can_create_update_and_deactivate_users(client, test_engine) -> None:
    admin = insert_test_user(
        test_engine,
        email="admin@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )
    headers = authenticate(client, admin.email, "SecurePass123")
    department_id = insert_test_department(test_engine)

    created = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "email": "manager@example.edu",
            "full_name": "Lab Manager",
            "password": "ManagerPass123",
            "role": "LAB_MANAGER",
            "department_id": str(department_id),
        },
    )

    assert created.status_code == 201
    user = created.json()
    assert user["role"] == "LAB_MANAGER"
    assert "hashed_password" not in user
    assert "password" not in user
    duplicate = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "email": "MANAGER@example.edu",
            "full_name": "Duplicate Manager",
            "password": "OtherPass123",
            "role": "LAB_MANAGER",
            "department_id": str(department_id),
        },
    )
    assert duplicate.status_code == 409
    manager_headers = authenticate(client, "manager@example.edu", "ManagerPass123")

    async def read_hash() -> str:
        factory = async_sessionmaker(test_engine, expire_on_commit=False)
        async with factory() as session:
            record = await session.scalar(
                select(User).where(User.email == "manager@example.edu")
            )
            assert record is not None
            return record.hashed_password

    stored_hash = asyncio.run(read_hash())
    assert stored_hash != "ManagerPass123"
    assert verify_password("ManagerPass123", stored_hash)

    updated = client.patch(
        f"/api/v1/users/{user['id']}",
        headers=headers,
        json={"full_name": "Updated Manager", "is_active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Updated Manager"
    assert updated.json()["is_active"] is False
    assert client.get(
        "/api/v1/auth/me",
        headers=manager_headers,
    ).status_code == 401


def test_admin_cannot_assign_unapproved_roles_or_unscoped_staff(
    client, test_engine
) -> None:
    admin = insert_test_user(
        test_engine,
        email="admin@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )
    headers = authenticate(client, admin.email, "SecurePass123")
    invalid_role = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "email": "new@example.edu",
            "full_name": "New User",
            "password": "SecurePass123",
            "role": "SYSTEM_ADMIN",
        },
    )
    unscoped_manager = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "email": "manager@example.edu",
            "full_name": "Manager",
            "password": "SecurePass123",
            "role": "LAB_MANAGER",
        },
    )

    assert invalid_role.status_code == 422
    assert unscoped_manager.status_code == 422


def test_admin_cannot_remove_the_last_active_admin(client, test_engine) -> None:
    admin = insert_test_user(
        test_engine,
        email="admin@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )
    headers = authenticate(client, admin.email, "SecurePass123")

    response = client.patch(
        f"/api/v1/users/{admin.id}",
        headers=headers,
        json={"is_active": False},
    )

    assert response.status_code == 409
