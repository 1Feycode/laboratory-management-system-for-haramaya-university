import asyncio
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.security import hash_password
from app.models import Asset, AssetAuditLog
from tests.conftest import insert_test_user


def _headers(client, user, password: str = "SecurePass123") -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _organization(client, headers, *, manager_id: str | None = None):
    college = client.post(
        "/api/v1/hierarchy/colleges",
        headers=headers,
        json={"name": "Engineering College", "code": "ENG"},
    )
    assert college.status_code == 201
    department = client.post(
        "/api/v1/hierarchy/departments",
        headers=headers,
        json={
            "college_id": college.json()["id"],
            "name": "Chemical Engineering",
            "code": "CHEM",
        },
    )
    assert department.status_code == 201
    laboratory = client.post(
        "/api/v1/hierarchy/laboratories",
        headers=headers,
        json={
            "department_id": department.json()["id"],
            "name": "Analytical Laboratory",
            "lab_type": "WET",
            "manager_id": manager_id,
        },
    )
    assert laboratory.status_code == 201
    room = client.post(
        "/api/v1/hierarchy/rooms",
        headers=headers,
        json={
            "laboratory_id": laboratory.json()["id"],
            "room_number": "B-14",
            "building_name": "Central Laboratory Building",
        },
    )
    assert room.status_code == 201
    return {
        "college": college.json(),
        "department": department.json(),
        "laboratory": laboratory.json(),
        "room": room.json(),
    }


def _category(client, headers):
    response = client.post(
        "/api/v1/asset-categories",
        headers=headers,
        json={
            "name": "Spectrophotometer",
            "requires_calibration": True,
            "default_calibration_interval_days": 180,
        },
    )
    assert response.status_code == 201
    return response.json()


def _asset_payload(category_id: str, org: dict, **overrides) -> dict:
    payload = {
        "serial_number": "SN-1001",
        "model_number": "UV-1900i",
        "manufacturer_name": "Shimadzu",
        "category_id": category_id,
        "laboratory_id": org["laboratory"]["id"],
        "room_id": org["room"]["id"],
        "purchase_date": "2025-09-15",
        "commissioning_date": "2025-10-01",
        "warranty_expiry_date": "2027-10-01",
    }
    return {**payload, **overrides}


def test_asset_registration_qr_lookup_and_pagination(client, test_engine) -> None:
    admin = insert_test_user(
        test_engine,
        email="admin@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )
    headers = _headers(client, admin)
    org = _organization(client, headers)
    category = _category(client, headers)

    created = client.post(
        "/api/v1/assets",
        headers=headers,
        json=_asset_payload(category["id"], org),
    )
    assert created.status_code == 201, created.text
    asset = created.json()
    assert asset["asset_code"] == "HU-ENG-CHEM-0001"
    assert asset["operational_status"] == "OPERATIONAL"
    assert asset["category_name"] == "Spectrophotometer"
    assert asset["college_name"] == "Engineering College"
    assert asset["next_calibration_due"] is None

    lookup = client.get(
        f"/api/v1/assets/lookup/{asset['asset_code']}", headers=headers
    )
    assert lookup.status_code == 200
    assert lookup.json()["id"] == asset["id"]

    qr = client.get(f"/api/v1/assets/{asset['id']}/qr", headers=headers)
    assert qr.status_code == 200
    assert qr.headers["content-type"].startswith("image/svg+xml")
    assert b"<svg" in qr.content

    second = client.post(
        "/api/v1/assets",
        headers=headers,
        json=_asset_payload(
            category["id"],
            org,
            serial_number="SN-1002",
            legacy_tag_number="OLD-TAG-02",
        ),
    )
    assert second.status_code == 201, second.text
    assert second.json()["asset_code"] == "HU-ENG-CHEM-0002"
    legacy_lookup = client.get(
        "/api/v1/assets/lookup/OLD-TAG-02", headers=headers
    )
    assert legacy_lookup.status_code == 200
    assert legacy_lookup.json()["id"] == second.json()["id"]

    third = client.post(
        "/api/v1/assets",
        headers=headers,
        json=_asset_payload(
            category["id"],
            org,
            serial_number="SN-1003",
            legacy_tag_number="OLD-TAG-02",
        ),
    )
    assert third.status_code == 201, third.text
    ambiguous_lookup = client.get(
        "/api/v1/assets/lookup/OLD-TAG-02", headers=headers
    )
    assert ambiguous_lookup.status_code == 409

    page = client.get(
        "/api/v1/assets",
        headers=headers,
        params={
            "search": "OLD-TAG-02",
            "category_id": category["id"],
            "laboratory_id": org["laboratory"]["id"],
            "status": "OPERATIONAL",
            "page": 1,
            "size": 1,
            "sort_by": "asset_code",
            "sort_order": "desc",
        },
    )
    assert page.status_code == 200
    assert page.json()["total"] == 2
    assert page.json()["items"][0]["id"] == third.json()["id"]

    assert (
        client.delete(f"/api/v1/assets/{asset['id']}", headers=headers).status_code
        == 405
    )


def test_asset_validation_serial_uniqueness_and_audit_snapshot(
    client, test_engine
) -> None:
    admin = insert_test_user(
        test_engine,
        email="admin@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )
    headers = _headers(client, admin)
    org = _organization(client, headers)
    category = _category(client, headers)
    payload = _asset_payload(category["id"], org)

    missing_category = client.post(
        "/api/v1/assets",
        headers=headers,
        json={**payload, "category_id": str(uuid4())},
    )
    assert missing_category.status_code == 422

    other_lab = client.post(
        "/api/v1/hierarchy/laboratories",
        headers=headers,
        json={
            "department_id": org["department"]["id"],
            "name": "Other Laboratory",
            "lab_type": "DRY",
        },
    ).json()
    mismatched_room = client.post(
        "/api/v1/assets",
        headers=headers,
        json={**payload, "laboratory_id": other_lab["id"]},
    )
    assert mismatched_room.status_code == 422

    created = client.post("/api/v1/assets", headers=headers, json=payload)
    assert created.status_code == 201, created.text
    duplicate = client.post("/api/v1/assets", headers=headers, json=payload)
    assert duplicate.status_code == 409

    updated = client.patch(
        f"/api/v1/assets/{created.json()['id']}",
        headers=headers,
        json={"model_number": "UV-1900i Updated", "purchase_date": None},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["model_number"] == "UV-1900i Updated"
    assert updated.json()["purchase_date"] is None

    async def read_audit_logs():
        factory = async_sessionmaker(test_engine, expire_on_commit=False)
        async with factory() as session:
            return list(
                (
                    await session.scalars(
                        select(AssetAuditLog)
                        .where(AssetAuditLog.entity_id == created.json()["id"])
                        .order_by(AssetAuditLog.id)
                    )
                ).all()
            )

    logs = asyncio.run(read_audit_logs())
    assert [entry.action for entry in logs] == ["ASSET_CREATED", "ASSET_UPDATED"]
    assert logs[0].new_values["asset_code"] == "HU-ENG-CHEM-0001"
    assert logs[1].old_values["model_number"] == "UV-1900i"
    assert logs[1].new_values["model_number"] == "UV-1900i Updated"


def test_asset_writes_require_assigned_lab_manager_or_admin(
    client, test_engine
) -> None:
    admin = insert_test_user(
        test_engine,
        email="admin@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )
    admin_headers = _headers(client, admin)
    college = client.post(
        "/api/v1/hierarchy/colleges",
        headers=admin_headers,
        json={"name": "Engineering College", "code": "ENG"},
    ).json()
    department = client.post(
        "/api/v1/hierarchy/departments",
        headers=admin_headers,
        json={
            "college_id": college["id"],
            "name": "Chemical Engineering",
            "code": "CHEM",
        },
    ).json()
    manager = insert_test_user(
        test_engine,
        email="manager@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="LAB_MANAGER",
        department_id=UUID(department["id"]),
    )
    manager_headers = _headers(client, manager)
    org = _organization_for_existing_department(
        client, admin_headers, department["id"], manager.id
    )
    category = _category(client, admin_headers)

    managed_asset = client.post(
        "/api/v1/assets",
        headers=manager_headers,
        json=_asset_payload(category["id"], org),
    )
    assert managed_asset.status_code == 201, managed_asset.text

    unassigned_laboratory = client.post(
        "/api/v1/hierarchy/laboratories",
        headers=admin_headers,
        json={
            "department_id": department["id"],
            "name": "Unassigned Laboratory",
            "lab_type": "DRY",
        },
    ).json()
    unassigned_room = client.post(
        "/api/v1/hierarchy/rooms",
        headers=admin_headers,
        json={
            "laboratory_id": unassigned_laboratory["id"],
            "room_number": "2",
            "building_name": "Engineering",
        },
    ).json()
    denied = client.post(
        "/api/v1/assets",
        headers=manager_headers,
        json=_asset_payload(
            category["id"],
            {
                **org,
                "laboratory": unassigned_laboratory,
                "room": unassigned_room,
            },
            serial_number="SN-OTHER",
        ),
    )
    assert denied.status_code == 403

    auditor = insert_test_user(
        test_engine,
        email="auditor@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="AUDITOR",
    )
    denied_role = client.post(
        "/api/v1/assets",
        headers=_headers(client, auditor),
        json=_asset_payload(category["id"], org, serial_number="SN-AUDIT"),
    )
    assert denied_role.status_code == 403


def test_category_administration_and_referential_delete_rules(
    client, test_engine
) -> None:
    admin = insert_test_user(
        test_engine,
        email="admin@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )
    headers = _headers(client, admin)
    org = _organization(client, headers)
    category = _category(client, headers)

    duplicate = client.post(
        "/api/v1/asset-categories",
        headers=headers,
        json={
            "name": category["name"],
            "requires_calibration": False,
            "default_calibration_interval_days": 0,
        },
    )
    assert duplicate.status_code == 409

    updated = client.patch(
        f"/api/v1/asset-categories/{category['id']}",
        headers=headers,
        json={"name": "Optical Instruments"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Optical Instruments"

    asset = client.post(
        "/api/v1/assets",
        headers=headers,
        json=_asset_payload(category["id"], org),
    )
    assert asset.status_code == 201
    used_category_delete = client.delete(
        f"/api/v1/asset-categories/{category['id']}", headers=headers
    )
    assert used_category_delete.status_code == 409

    unused = client.post(
        "/api/v1/asset-categories",
        headers=headers,
        json={
            "name": "Unused Category",
            "requires_calibration": False,
            "default_calibration_interval_days": 0,
        },
    ).json()
    unused_delete = client.delete(
        f"/api/v1/asset-categories/{unused['id']}", headers=headers
    )
    assert unused_delete.status_code == 204

    async def read_category_audit():
        factory = async_sessionmaker(test_engine, expire_on_commit=False)
        async with factory() as session:
            return list(
                (
                    await session.scalars(
                        select(AssetAuditLog.action)
                        .where(
                            AssetAuditLog.entity_type == "asset_categories",
                            AssetAuditLog.entity_id == unused["id"],
                        )
                        .order_by(AssetAuditLog.id)
                    )
                ).all()
            )

    assert asyncio.run(read_category_audit()) == [
        "ASSET_CATEGORY_CREATED",
        "ASSET_CATEGORY_DELETED",
    ]


def test_asset_registration_locks_identity_and_room_hierarchy(
    client, test_engine
) -> None:
    admin = insert_test_user(
        test_engine,
        email="admin@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )
    headers = _headers(client, admin)
    org = _organization(client, headers)
    category = _category(client, headers)
    asset = client.post(
        "/api/v1/assets",
        headers=headers,
        json=_asset_payload(category["id"], org),
    )
    assert asset.status_code == 201

    other_college = client.post(
        "/api/v1/hierarchy/colleges",
        headers=headers,
        json={"name": "Other College", "code": "OTHER"},
    ).json()
    other_department = client.post(
        "/api/v1/hierarchy/departments",
        headers=headers,
        json={
            "college_id": other_college["id"],
            "name": "Other Department",
            "code": "OTHER",
        },
    ).json()
    other_laboratory = client.post(
        "/api/v1/hierarchy/laboratories",
        headers=headers,
        json={
            "department_id": other_department["id"],
            "name": "Other Laboratory",
            "lab_type": "DRY",
        },
    ).json()

    assert client.patch(
        f"/api/v1/hierarchy/colleges/{org['college']['id']}",
        headers=headers,
        json={"code": "ENG2"},
    ).status_code == 409
    assert client.patch(
        f"/api/v1/hierarchy/departments/{org['department']['id']}",
        headers=headers,
        json={"code": "CHEM2"},
    ).status_code == 409
    assert client.patch(
        f"/api/v1/hierarchy/departments/{org['department']['id']}",
        headers=headers,
        json={"college_id": other_college["id"]},
    ).status_code == 409
    assert client.patch(
        f"/api/v1/hierarchy/laboratories/{org['laboratory']['id']}",
        headers=headers,
        json={"department_id": other_department["id"]},
    ).status_code == 409
    assert client.patch(
        f"/api/v1/hierarchy/rooms/{org['room']['id']}",
        headers=headers,
        json={"laboratory_id": other_laboratory["id"]},
    ).status_code == 409


def test_asset_code_limit_returns_conflict(client, test_engine) -> None:
    admin = insert_test_user(
        test_engine,
        email="admin@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )
    headers = _headers(client, admin)
    org = _organization(client, headers)
    category = _category(client, headers)
    asset = client.post(
        "/api/v1/assets",
        headers=headers,
        json=_asset_payload(category["id"], org),
    )
    assert asset.status_code == 201

    async def set_last_code():
        factory = async_sessionmaker(test_engine, expire_on_commit=False)
        async with factory() as session:
            await session.execute(
                update(Asset)
                .where(Asset.id == UUID(asset.json()["id"]))
                .values(asset_code="HU-ENG-CHEM-9999")
            )
            await session.commit()

    asyncio.run(set_last_code())
    overflow = client.post(
        "/api/v1/assets",
        headers=headers,
        json=_asset_payload(category["id"], org, serial_number="SN-1002"),
    )
    assert overflow.status_code == 409
    assert "four-digit" in overflow.json()["detail"]


def _organization_for_existing_department(client, headers, department_id, manager_id):
    laboratory = client.post(
        "/api/v1/hierarchy/laboratories",
        headers=headers,
        json={
            "department_id": department_id,
            "name": "Managed Laboratory",
            "lab_type": "WET",
            "manager_id": str(manager_id),
        },
    )
    assert laboratory.status_code == 201
    room = client.post(
        "/api/v1/hierarchy/rooms",
        headers=headers,
        json={
            "laboratory_id": laboratory.json()["id"],
            "room_number": "B-14",
            "building_name": "Central Laboratory Building",
        },
    )
    assert room.status_code == 201
    college = client.get(
        f"/api/v1/hierarchy/departments/{department_id}", headers=headers
    ).json()
    return {
        "college": {"id": college["college_id"]},
        "department": college,
        "laboratory": laboratory.json(),
        "room": room.json(),
    }
