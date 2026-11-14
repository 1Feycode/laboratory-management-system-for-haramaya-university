import asyncio
import csv
from datetime import date, timedelta
import io
import uuid

from sqlalchemy import insert

from app.core.security import hash_password
from app.models.asset import Asset
from app.services.report_service import _csv_cell
from sqlalchemy.ext.asyncio import async_sessionmaker
from tests.conftest import insert_test_user
from tests.test_maintenance import (
    _add_log,
    _assign_and_start,
    _headers,
    _maintenance_setup,
    _report,
)


def _dashboard(client, headers, **params):
    return client.get(
        "/api/v1/reports/dashboard",
        headers=headers,
        params=params,
    )


def test_dashboard_scopes_metrics_and_calibration_status(client, test_engine) -> None:
    setup = _maintenance_setup(client, test_engine)
    admin_headers = setup["admin_headers"]
    department_id = setup["manager"].department_id

    second_lab = client.post(
        "/api/v1/hierarchy/laboratories",
        headers=admin_headers,
        json={
            "department_id": str(department_id),
            "name": "Unmanaged Reporting Laboratory",
            "lab_type": "DRY",
        },
    )
    assert second_lab.status_code == 201, second_lab.text
    second_room = client.post(
        "/api/v1/hierarchy/rooms",
        headers=admin_headers,
        json={
            "laboratory_id": second_lab.json()["id"],
            "room_number": "R-02",
            "building_name": "Reporting Building",
        },
    )
    assert second_room.status_code == 201, second_room.text
    second_asset = client.post(
        "/api/v1/assets",
        headers=admin_headers,
        json={
            "serial_number": "SN-REPORT-02",
            "model_number": "Model-R2",
            "manufacturer_name": " =2+2",
            "category_id": setup["asset"]["category_id"],
            "laboratory_id": second_lab.json()["id"],
            "room_id": second_room.json()["id"],
        },
    )
    assert second_asset.status_code == 201, second_asset.text

    calibration = client.post(
        "/api/v1/calibrations",
        headers=admin_headers,
        json={
            "asset_id": setup["asset"]["id"],
            "calibration_date": (date.today() - timedelta(days=200)).isoformat(),
            "standard_used": "Reporting test standard",
            "passed": True,
        },
    )
    assert calibration.status_code == 201, calibration.text

    work_order = _report(
        client,
        setup,
        headers=admin_headers,
        severity="CRITICAL",
    )
    assert work_order.status_code == 201, work_order.text
    completed_order = client.post(
        "/api/v1/work-orders",
        headers=admin_headers,
        json={
            "asset_id": second_asset.json()["id"],
            "severity": "HIGH",
            "failure_category": "OPTICAL",
            "fault_description": "Reporting test repair.",
        },
    )
    assert completed_order.status_code == 201, completed_order.text
    _assign_and_start(client, setup, completed_order.json())
    maintenance_log = _add_log(client, setup, completed_order.json()["id"])
    assert maintenance_log.status_code == 201, maintenance_log.text
    closed_order = client.put(
        f"/api/v1/work-orders/{completed_order.json()['id']}/close",
        headers=admin_headers,
        json={
            "confirmed": True,
            "verification_notes": "Verified for reporting integration test.",
        },
    )
    assert closed_order.status_code == 200, closed_order.text
    upcoming_calibration = client.post(
        "/api/v1/calibrations",
        headers=admin_headers,
        json={
            "asset_id": second_asset.json()["id"],
            "calibration_date": (date.today() - timedelta(days=175)).isoformat(),
            "standard_used": "Reporting test standard",
            "passed": True,
        },
    )
    assert upcoming_calibration.status_code == 201, upcoming_calibration.text

    today = date.today().isoformat()
    admin_report = _dashboard(
        client,
        admin_headers,
        within_days=7,
        date_from=today,
        date_to=today,
    )
    assert admin_report.status_code == 200, admin_report.text
    data = admin_report.json()
    assert data["asset_total"] == 2
    assert data["operational_assets"] == 1
    assert data["work_order_total"] == 2
    assert data["active_work_orders"] == 1
    assert data["work_orders_completed"] == 1
    assert data["calibration_records"] == 0
    assert data["overdue_calibrations"] == 1
    assert data["upcoming_calibrations"] == 1
    assert data["critical_work_orders"][0]["id"] == work_order.json()["id"]
    assert data["availability_status"] == "PENDING_APPROVED_DEFINITION"
    assert data["uptime_percentage"] is None
    assert data["downtime_asset_hours"] is None

    downtime_report = client.get(
        "/api/v1/reports/downtime",
        headers=admin_headers,
        params={"date_from": today, "date_to": today},
    )
    assert downtime_report.status_code == 200, downtime_report.text
    downtime_data = downtime_report.json()
    assert downtime_data["work_order_requests"] == 2
    assert downtime_data["work_orders_completed"] == 1
    assert downtime_data["active_work_orders"] == 1
    assert downtime_data["uptime_percentage"] is None
    assert downtime_data["downtime_asset_hours"] is None

    calibration_report = client.get(
        "/api/v1/reports/calibration-compliance",
        headers=admin_headers,
        params={"within_days": 7},
    )
    assert calibration_report.status_code == 200, calibration_report.text
    calibration_data = calibration_report.json()
    assert calibration_data["calibration_records"] == 2
    assert calibration_data["calibrations_passed"] == 2
    assert calibration_data["overdue_calibrations"] == 1
    assert calibration_data["upcoming_calibrations"] == 1
    no_upcoming = client.get(
        "/api/v1/reports/calibration-compliance",
        headers=admin_headers,
        params={"within_days": 0},
    )
    assert no_upcoming.status_code == 200, no_upcoming.text
    assert no_upcoming.json()["upcoming_calibrations"] == 0

    manager_report = _dashboard(
        client, setup["manager_headers"], within_days=7
    )
    assert manager_report.status_code == 200, manager_report.text
    assert manager_report.json()["asset_total"] == 1
    assert manager_report.json()["work_order_total"] == 1
    inventory_export = client.get(
        "/api/v1/reports/inventory",
        headers=admin_headers,
        params={"status": "OPERATIONAL"},
    )
    assert inventory_export.status_code == 200, inventory_export.text
    assert second_asset.json()["asset_code"] in inventory_export.text
    assert setup["asset"]["asset_code"] not in inventory_export.text
    assert "'=2+2" in inventory_export.text
    assert _csv_cell(" =2+2") == "' =2+2"

    auditor = insert_test_user(
        test_engine,
        email="reports-auditor@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="AUDITOR",
        department_id=department_id,
    )
    auditor_report = _dashboard(
        client, _headers(client, auditor), within_days=7
    )
    assert auditor_report.status_code == 200, auditor_report.text
    assert auditor_report.json()["asset_total"] == 2

    technician_report = _dashboard(
        client, setup["technician_headers"], within_days=7
    )
    assert technician_report.status_code == 403


def test_reports_validation_empty_scope_and_inventory_csv(client, test_engine) -> None:
    setup = _maintenance_setup(client, test_engine)
    headers = setup["admin_headers"]

    partial_period = _dashboard(
        client,
        headers,
        within_days=7,
        date_from=date.today().isoformat(),
    )
    assert partial_period.status_code == 422

    empty = _dashboard(
        client, headers, college_id=str(uuid.uuid4()), within_days=7
    )
    assert empty.status_code == 200, empty.text
    assert empty.json()["asset_total"] == 0
    assert empty.json()["assets_by_status"] == []
    assert empty.json()["critical_work_orders"] == []

    export = client.get("/api/v1/reports/inventory", headers=headers)
    assert export.status_code == 200, export.text
    assert "text/csv" in export.headers["content-type"]
    assert "Asset Code" in export.text
    assert setup["asset"]["asset_code"] in export.text

    manager_export = client.get(
        "/api/v1/reports/inventory",
        headers=setup["manager_headers"],
    )
    assert manager_export.status_code == 403


def test_inventory_csv_handles_large_result_set(client, test_engine) -> None:
    setup = _maintenance_setup(client, test_engine)
    asset = setup["asset"]
    rows = [
        {
            "asset_code": f"REPORT-BULK-{index:04d}",
            "serial_number": f"REPORT-BULK-SN-{index:04d}",
            "model_number": "Reporting Test Model",
            "manufacturer_name": "Reporting Test Manufacturer",
            "category_id": uuid.UUID(asset["category_id"]),
            "laboratory_id": uuid.UUID(asset["laboratory_id"]),
            "room_id": uuid.UUID(asset["room_id"]),
        }
        for index in range(1000)
    ]

    async def insert_assets() -> None:
        async with test_engine.begin() as connection:
            await connection.execute(insert(Asset.__table__), rows)

    asyncio.run(insert_assets())
    response = client.get(
        "/api/v1/reports/inventory",
        headers=setup["admin_headers"],
    )

    assert response.status_code == 200, response.text
    records = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig"))))
    assert len(records) == 1002
