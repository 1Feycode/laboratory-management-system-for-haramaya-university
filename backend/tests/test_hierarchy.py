import asyncio
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.security import hash_password
from app.models.user import User
from tests.conftest import insert_test_user


def _headers(client, user) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": "SecurePass123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_hierarchy_crud_search_pagination_and_duplicate_validation(
    client, test_engine
) -> None:
    admin = insert_test_user(
        test_engine,
        email="admin@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )
    headers = _headers(client, admin)

    college = client.post(
        "/api/v1/hierarchy/colleges",
        headers=headers,
        json={"name": "College of Engineering", "code": "ENG"},
    )
    assert college.status_code == 201
    college_id = college.json()["id"]
    duplicate_college = client.post(
        "/api/v1/hierarchy/colleges",
        headers=headers,
        json={"name": "College of Engineering", "code": "ENG2"},
    )
    assert duplicate_college.status_code == 409

    department = client.post(
        "/api/v1/hierarchy/departments",
        headers=headers,
        json={
            "college_id": college_id,
            "name": "Chemical Engineering",
            "code": "CHEM",
        },
    )
    assert department.status_code == 201
    department_id = department.json()["id"]
    department_update = client.patch(
        f"/api/v1/hierarchy/departments/{department_id}",
        headers=headers,
        json={"name": "Chemical and Process Engineering"},
    )
    assert department_update.status_code == 200
    assert department_update.json()["name"] == "Chemical and Process Engineering"
    duplicate_department = client.post(
        "/api/v1/hierarchy/departments",
        headers=headers,
        json={
            "college_id": college_id,
            "name": "Different department name",
            "code": "CHEM",
        },
    )
    assert duplicate_department.status_code == 409

    laboratory = client.post(
        "/api/v1/hierarchy/laboratories",
        headers=headers,
        json={
            "department_id": department_id,
            "name": "Analytical Lab",
            "lab_type": "WET",
        },
    )
    assert laboratory.status_code == 201
    laboratory_id = laboratory.json()["id"]
    laboratory_update = client.patch(
        f"/api/v1/hierarchy/laboratories/{laboratory_id}",
        headers=headers,
        json={"lab_type": "COMPUTING"},
    )
    assert laboratory_update.status_code == 200
    assert laboratory_update.json()["lab_type"] == "COMPUTING"
    room = client.post(
        "/api/v1/hierarchy/rooms",
        headers=headers,
        json={
            "laboratory_id": laboratory_id,
            "room_number": "B-14",
            "building_name": "Central Laboratory",
        },
    )
    assert room.status_code == 201

    duplicate_room = client.post(
        "/api/v1/hierarchy/rooms",
        headers=headers,
        json={
            "laboratory_id": laboratory_id,
            "room_number": "B-14",
            "building_name": "Other building",
        },
    )
    assert duplicate_room.status_code == 409

    updated = client.patch(
        f"/api/v1/hierarchy/rooms/{room.json()['id']}",
        headers=headers,
        json={"building_name": "New Laboratory Building"},
    )
    assert updated.status_code == 200
    assert updated.json()["building_name"] == "New Laboratory Building"
    assert updated.json()["college_name"] == "College of Engineering"

    page = client.get(
        "/api/v1/hierarchy/laboratories",
        headers=headers,
        params={"search": "Analytical", "page": 1, "size": 1},
    )
    assert page.status_code == 200
    assert page.json()["total"] == 1
    assert page.json()["items"][0]["id"] == laboratory_id

    assert (
        client.get(
            f"/api/v1/hierarchy/departments/{department_id}",
            headers=headers,
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/api/v1/hierarchy/colleges/{college_id}",
            headers=headers,
            json={"name": "Updated Engineering College"},
        ).status_code
        == 200
    )


def test_hierarchy_relationships_permissions_and_referential_integrity(
    client, test_engine
) -> None:
    admin = insert_test_user(
        test_engine,
        email="admin@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )
    auditor = insert_test_user(
        test_engine,
        email="auditor@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="AUDITOR",
    )
    admin_headers = _headers(client, admin)
    auditor_headers = _headers(client, auditor)

    assert client.get("/api/v1/hierarchy/colleges").status_code == 401
    assert client.get(
        "/api/v1/hierarchy/colleges", headers=auditor_headers
    ).status_code == 200
    assert client.post(
        "/api/v1/hierarchy/colleges",
        headers=auditor_headers,
        json={"name": "Unauthorized", "code": "NO"},
    ).status_code == 403

    invalid_department = client.post(
        "/api/v1/hierarchy/departments",
        headers=admin_headers,
        json={
            "college_id": str(uuid4()),
            "name": "Orphan",
            "code": "ORPH",
        },
    )
    assert invalid_department.status_code == 422
    invalid_laboratory = client.post(
        "/api/v1/hierarchy/laboratories",
        headers=admin_headers,
        json={
            "department_id": str(uuid4()),
            "name": "Orphan laboratory",
            "lab_type": "WET",
        },
    )
    invalid_room = client.post(
        "/api/v1/hierarchy/rooms",
        headers=admin_headers,
        json={
            "laboratory_id": str(uuid4()),
            "room_number": "1",
            "building_name": "Nowhere",
        },
    )
    assert invalid_laboratory.status_code == 422
    assert invalid_room.status_code == 422

    college = client.post(
        "/api/v1/hierarchy/colleges",
        headers=admin_headers,
        json={"name": "College", "code": "COL"},
    ).json()
    department = client.post(
        "/api/v1/hierarchy/departments",
        headers=admin_headers,
        json={
            "college_id": college["id"],
            "name": "Department",
            "code": "DEP",
        },
    ).json()
    laboratory = client.post(
        "/api/v1/hierarchy/laboratories",
        headers=admin_headers,
        json={
            "department_id": department["id"],
            "name": "Laboratory",
            "lab_type": "COMPUTING",
        },
    ).json()
    invalid_lab_type = client.post(
        "/api/v1/hierarchy/laboratories",
        headers=admin_headers,
        json={
            "department_id": department["id"],
            "name": "Invalid type",
            "lab_type": "CLINICAL",
        },
    )
    assert invalid_lab_type.status_code == 422
    room = client.post(
        "/api/v1/hierarchy/rooms",
        headers=admin_headers,
        json={
            "laboratory_id": laboratory["id"],
            "room_number": "1",
            "building_name": "Building",
        },
    ).json()

    assert (
        client.delete(
            f"/api/v1/hierarchy/laboratories/{laboratory['id']}",
            headers=admin_headers,
        ).status_code
        == 409
    )
    assert (
        client.delete(
            f"/api/v1/hierarchy/departments/{department['id']}",
            headers=admin_headers,
        ).status_code
        == 409
    )
    assert (
        client.delete(
            f"/api/v1/hierarchy/colleges/{college['id']}",
            headers=admin_headers,
        ).status_code
        == 409
    )
    assert (
        client.delete(
            f"/api/v1/hierarchy/rooms/{room['id']}",
            headers=admin_headers,
        ).status_code
        == 204
    )
    assert (
        client.delete(
            f"/api/v1/hierarchy/laboratories/{laboratory['id']}",
            headers=admin_headers,
        ).status_code
        == 204
    )


def test_department_delete_applies_approved_user_set_null_action(
    client, test_engine
) -> None:
    admin = insert_test_user(
        test_engine,
        email="admin@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )
    headers = _headers(client, admin)
    college = client.post(
        "/api/v1/hierarchy/colleges",
        headers=headers,
        json={"name": "College", "code": "COL"},
    ).json()
    department = client.post(
        "/api/v1/hierarchy/departments",
        headers=headers,
        json={
            "college_id": college["id"],
            "name": "Department",
            "code": "DEP",
        },
    ).json()
    manager = insert_test_user(
        test_engine,
        email="manager@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="LAB_MANAGER",
        department_id=UUID(department["id"]),
    )

    deleted = client.delete(
        f"/api/v1/hierarchy/departments/{department['id']}",
        headers=headers,
    )
    assert deleted.status_code == 204

    async def read_department_assignment():
        factory = async_sessionmaker(test_engine, expire_on_commit=False)
        async with factory() as session:
            return await session.scalar(
                select(User.department_id).where(User.id == manager.id)
            )

    assert asyncio.run(read_department_assignment()) is None
