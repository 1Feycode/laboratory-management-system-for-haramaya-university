import asyncio
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.security import hash_password
from app.models import AssetAuditLog, CalibrationLog
from tests.conftest import insert_test_user


def _headers(client, user, password: str = "SecurePass123") -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _organization(client, headers):
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
            "manager_id": None,
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
    return laboratory.json(), room.json()


def _create_category(client, headers, name, requires_calibration, interval_days):
    response = client.post(
        "/api/v1/asset-categories",
        headers=headers,
        json={
            "name": name,
            "requires_calibration": requires_calibration,
            "default_calibration_interval_days": interval_days,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_asset(client, headers, category, laboratory, room, serial):
    response = client.post(
        "/api/v1/assets",
        headers=headers,
        json={
            "serial_number": serial,
            "model_number": "UV-1900i",
            "manufacturer_name": "Shimadzu",
            "category_id": category["id"],
            "laboratory_id": laboratory["id"],
            "room_id": room["id"],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _calibration_payload(asset_id, calibration_date, *, passed=True):
    return {
        "asset_id": asset_id,
        "calibration_date": calibration_date.isoformat(),
        "standard_used": "Traceable absorbance standard",
        "certificate_reference": "CERT-2026-01",
        "accreditation_body": None,
        "passed": passed,
        "notes": "Bench verification",
    }


def test_calibration_updates_asset_and_preserves_append_only_history(
    client, test_engine
) -> None:
    admin = insert_test_user(
        test_engine,
        email="calibration-admin@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )
    auditor = insert_test_user(
        test_engine,
        email="calibration-auditor@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="AUDITOR",
    )
    headers = _headers(client, admin)
    org_lab, room = _organization(client, headers)
    category = _create_category(client, headers, "Spectrophotometer", True, 180)
    asset = _create_asset(client, headers, category, org_lab, room, "CAL-SN-01")

    calibration_date = date.today() - timedelta(days=200)
    created = client.post(
        "/api/v1/calibrations",
        headers=headers,
        json=_calibration_payload(asset["id"], calibration_date),
    )
    assert created.status_code == 201, created.text
    first = created.json()
    assert first["next_due_date"] == (
        calibration_date + timedelta(days=180)
    ).isoformat()

    current_asset = client.get(f"/api/v1/assets/{asset['id']}", headers=headers)
    assert current_asset.status_code == 200
    assert current_asset.json()["last_calibrated_date"] == calibration_date.isoformat()
    assert current_asset.json()["calibration_overdue"] is True

    old_due_date = current_asset.json()["next_calibration_due"]
    failed_date = date.today() - timedelta(days=1)
    failed = client.post(
        "/api/v1/calibrations",
        headers=headers,
        json=_calibration_payload(asset["id"], failed_date, passed=False),
    )
    assert failed.status_code == 201, failed.text
    assert failed.json()["passed"] is False
    assert failed.json()["next_due_date"] == (
        failed_date + timedelta(days=180)
    ).isoformat()

    updated_asset = client.get(f"/api/v1/assets/{asset['id']}", headers=headers)
    assert updated_asset.json()["last_calibrated_date"] == failed_date.isoformat()
    assert updated_asset.json()["next_calibration_due"] == old_due_date
    assert updated_asset.json()["calibration_overdue"] is True

    due = client.get(
        "/api/v1/calibrations/due",
        headers=_headers(client, auditor),
        params={"within_days": 0},
    )
    assert due.status_code == 200
    assert due.json()["total"] == 1
    assert due.json()["items"][0]["status"] == "OVERDUE"

    history = client.get("/api/v1/calibrations", headers=_headers(client, auditor))
    assert history.status_code == 200
    assert history.json()["total"] == 2
    assert {item["id"] for item in history.json()["items"]} == {
        first["id"],
        failed.json()["id"],
    }

    async def counts():
        factory = async_sessionmaker(test_engine, expire_on_commit=False)
        async with factory() as session:
            log_count = await session.scalar(
                select(func.count(CalibrationLog.id)).where(
                    CalibrationLog.asset_id == asset["id"]
                )
            )
            audit_count = await session.scalar(
                select(func.count(AssetAuditLog.id)).where(
                    AssetAuditLog.entity_type == "calibration_logs"
                )
            )
            return log_count, audit_count

    log_count, audit_count = asyncio.run(counts())
    assert log_count == 2
    assert audit_count == 2


def test_calibration_authorization_and_category_validation(client, test_engine) -> None:
    admin = insert_test_user(
        test_engine,
        email="calibration-admin-2@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="ULMD_ADMIN",
    )
    manager = insert_test_user(
        test_engine,
        email="calibration-manager@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="LAB_MANAGER",
    )
    technician = insert_test_user(
        test_engine,
        email="calibration-technician@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="MAINTENANCE_TECH",
    )
    headers = _headers(client, admin)
    org_lab, room = _organization(client, headers)
    category = _create_category(client, headers, "Balance", True, 365)
    asset = _create_asset(client, headers, category, org_lab, room, "CAL-SN-02")
    payload = _calibration_payload(asset["id"], date.today())

    denied = client.post(
        "/api/v1/calibrations",
        headers=_headers(client, manager),
        json=payload,
    )
    assert denied.status_code == 403
    assert client.get("/api/v1/calibrations", headers=_headers(client, manager)).status_code == 403
    assert client.get("/api/v1/calibrations/due", headers=headers).status_code == 422
    out_of_range = client.get(
        "/api/v1/calibrations/due",
        headers=headers,
        params={"within_days": 999999999},
    )
    assert out_of_range.status_code == 422

    technician_record = client.post(
        "/api/v1/calibrations",
        headers=_headers(client, technician),
        json=payload,
    )
    assert technician_record.status_code == 201, technician_record.text

    invalid_standard = client.post(
        "/api/v1/calibrations",
        headers=headers,
        json={**payload, "standard_used": "  "},
    )
    assert invalid_standard.status_code == 422

    missing_asset = client.post(
        "/api/v1/calibrations",
        headers=headers,
        json=_calibration_payload(str(uuid4()), date.today()),
    )
    assert missing_asset.status_code == 404

    not_required = _create_category(
        client, headers, "Microscope", False, 0
    )
    non_calibrated_asset = _create_asset(
        client, headers, not_required, org_lab, room, "CAL-SN-03"
    )
    rejected = client.post(
        "/api/v1/calibrations",
        headers=headers,
        json=_calibration_payload(non_calibrated_asset["id"], date.today()),
    )
    assert rejected.status_code == 409

    no_interval = _create_category(
        client, headers, "Autoclave", True, 0
    )
    no_interval_asset = _create_asset(
        client, headers, no_interval, org_lab, room, "CAL-SN-04"
    )
    rejected_interval = client.post(
        "/api/v1/calibrations",
        headers=headers,
        json=_calibration_payload(no_interval_asset["id"], date.today()),
    )
    assert rejected_interval.status_code == 409
    assert client.patch(
        "/api/v1/calibrations",
        headers=headers,
        json={"notes": "overwrite"},
    ).status_code == 405
