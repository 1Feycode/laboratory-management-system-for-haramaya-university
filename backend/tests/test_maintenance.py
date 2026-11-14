import asyncio
import re
import uuid

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.asset import Asset, AssetAuditLog
from app.models.maintenance import MaintenanceLog, WorkOrder
from app.services import maintenance_service
from tests.conftest import insert_test_user


def _headers(client, user) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": "SecurePass123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _maintenance_setup(client, test_engine):
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
            "name": "Engineering Department",
            "code": "ENG",
        },
    ).json()
    department_id = uuid.UUID(department["id"])
    manager = insert_test_user(
        test_engine,
        email="manager@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="LAB_MANAGER",
        department_id=department_id,
    )
    lab_tech = insert_test_user(
        test_engine,
        email="labtech@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="LAB_TECH",
        department_id=department_id,
    )
    technician = insert_test_user(
        test_engine,
        email="maintenance@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="MAINTENANCE_TECH",
    )
    other_technician = insert_test_user(
        test_engine,
        email="other-maintenance@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="MAINTENANCE_TECH",
    )
    manager_headers = _headers(client, manager)
    lab_tech_headers = _headers(client, lab_tech)
    technician_headers = _headers(client, technician)
    other_technician_headers = _headers(client, other_technician)

    laboratory = client.post(
        "/api/v1/hierarchy/laboratories",
        headers=admin_headers,
        json={
            "department_id": department["id"],
            "name": "Analytical Laboratory",
            "lab_type": "WET",
            "manager_id": str(manager.id),
        },
    )
    assert laboratory.status_code == 201, laboratory.text
    lab = laboratory.json()
    room = client.post(
        "/api/v1/hierarchy/rooms",
        headers=admin_headers,
        json={
            "laboratory_id": lab["id"],
            "room_number": "A-10",
            "building_name": "Central Laboratory Building",
        },
    )
    assert room.status_code == 201, room.text
    category = client.post(
        "/api/v1/asset-categories",
        headers=admin_headers,
        json={
            "name": "Spectrophotometer",
            "requires_calibration": True,
            "default_calibration_interval_days": 180,
        },
    )
    assert category.status_code == 201, category.text
    asset = client.post(
        "/api/v1/assets",
        headers=admin_headers,
        json={
            "serial_number": "SN-MAINTENANCE-01",
            "model_number": "UV-1900i",
            "manufacturer_name": "Shimadzu",
            "category_id": category.json()["id"],
            "laboratory_id": lab["id"],
            "room_id": room.json()["id"],
        },
    )
    assert asset.status_code == 201, asset.text
    return {
        "admin": admin,
        "admin_headers": admin_headers,
        "manager": manager,
        "manager_headers": manager_headers,
        "lab_tech": lab_tech,
        "lab_tech_headers": lab_tech_headers,
        "technician": technician,
        "technician_headers": technician_headers,
        "other_technician": other_technician,
        "other_technician_headers": other_technician_headers,
        "asset": asset.json(),
    }


def _report_payload(asset_id: str, **overrides) -> dict:
    return {
        "asset_id": asset_id,
        "severity": "HIGH",
        "failure_category": "OPTICAL",
        "fault_description": "The instrument fails its initialization self-test.",
        **overrides,
    }


def _report(client, setup, *, headers=None, **overrides):
    return client.post(
        "/api/v1/work-orders",
        headers=headers or setup["lab_tech_headers"],
        json=_report_payload(setup["asset"]["id"], **overrides),
    )


def _assign_and_start(client, setup, order):
    assigned = client.put(
        f"/api/v1/work-orders/{order['id']}/assign",
        headers=setup["admin_headers"],
        json={"assigned_to": str(setup["technician"].id)},
    )
    assert assigned.status_code == 200, assigned.text
    started = client.put(
        f"/api/v1/work-orders/{order['id']}/status",
        headers=setup["technician_headers"],
        json={"status": "IN_PROGRESS"},
    )
    assert started.status_code == 200, started.text
    return started.json()


def _add_log(client, setup, order_id, *, outcome="OPERATIONAL", actions=None):
    return client.post(
        f"/api/v1/work-orders/{order_id}/logs",
        headers=setup["technician_headers"],
        json={
            "actions_taken": actions or "Replaced the lamp and verified the baseline.",
            "spare_parts_used": "Lamp assembly",
            "labor_hours": "1.50",
            "outcome_condition": outcome,
        },
    )


def test_maintenance_request_assignment_repair_verification_and_history(
    client, test_engine
) -> None:
    setup = _maintenance_setup(client, test_engine)

    created = _report(client, setup)
    assert created.status_code == 201, created.text
    order = created.json()
    assert re.fullmatch(r"WO-\d{4}-\d{4,}", order["ticket_number"])
    assert order["status"] == "OPEN"
    assert order["reporter_name"] == setup["lab_tech"].full_name
    assert order["status_history"][0]["new_status"] == "OPEN"

    asset = client.get(
        f"/api/v1/assets/{setup['asset']['id']}",
        headers=setup["admin_headers"],
    ).json()
    assert asset["operational_status"] == "UNDER_MAINTENANCE"

    assigned = client.put(
        f"/api/v1/work-orders/{order['id']}/assign",
        headers=setup["admin_headers"],
        json={"assigned_to": str(setup["technician"].id)},
    )
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["status"] == "ASSIGNED"
    assert assigned.json()["assignee_name"] == setup["technician"].full_name

    unauthorized = client.put(
        f"/api/v1/work-orders/{order['id']}/status",
        headers=setup["other_technician_headers"],
        json={"status": "IN_PROGRESS"},
    )
    assert unauthorized.status_code == 403

    started = client.put(
        f"/api/v1/work-orders/{order['id']}/status",
        headers=setup["technician_headers"],
        json={"status": "IN_PROGRESS"},
    )
    assert started.status_code == 200
    assert started.json()["status"] == "IN_PROGRESS"

    completed_work = _add_log(client, setup, order["id"])
    assert completed_work.status_code == 201, completed_work.text
    resolved = completed_work.json()
    assert resolved["status"] == "RESOLVED"
    assert len(resolved["maintenance_logs"]) == 1
    assert resolved["maintenance_logs"][0]["technician_id"] == str(
        setup["technician"].id
    )
    assert resolved["maintenance_logs"][0]["labor_hours"] == "1.50"

    closed = client.put(
        f"/api/v1/work-orders/{order['id']}/close",
        headers=setup["manager_headers"],
        json={
            "confirmed": True,
            "verification_notes": "Verified normal operation with a reference sample.",
        },
    )
    assert closed.status_code == 200, closed.text
    assert closed.json()["status"] == "CLOSED"
    assert closed.json()["verifier_name"] == setup["manager"].full_name
    assert [
        event["new_status"] for event in closed.json()["status_history"]
    ] == ["OPEN", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "CLOSED"]

    final_asset = client.get(
        f"/api/v1/assets/{setup['asset']['id']}",
        headers=setup["admin_headers"],
    ).json()
    assert final_asset["operational_status"] == "OPERATIONAL"

    listed = client.get(
        "/api/v1/work-orders",
        headers=setup["admin_headers"],
        params={"asset_id": setup["asset"]["id"], "status": "CLOSED"},
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == order["id"]


def test_critical_fault_locks_asset_and_rejects_duplicate_active_request(
    client, test_engine
) -> None:
    setup = _maintenance_setup(client, test_engine)
    created = _report(
        client,
        setup,
        severity="CRITICAL",
        failure_category="ELECTRICAL",
    )
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "OPEN"

    asset = client.get(
        f"/api/v1/assets/{setup['asset']['id']}",
        headers=setup["admin_headers"],
    ).json()
    assert asset["operational_status"] == "DEFECTIVE"

    duplicate = _report(client, setup)
    assert duplicate.status_code == 409
    assert "DEFECTIVE status" in duplicate.json()["detail"]


def test_invalid_assignment_parts_cycle_and_manager_rejection(
    client, test_engine
) -> None:
    setup = _maintenance_setup(client, test_engine)
    order = _report(client, setup).json()

    wrong_role = client.put(
        f"/api/v1/work-orders/{order['id']}/assign",
        headers=setup["admin_headers"],
        json={"assigned_to": str(setup["manager"].id)},
    )
    assert wrong_role.status_code == 422

    assigned = client.put(
        f"/api/v1/work-orders/{order['id']}/assign",
        headers=setup["admin_headers"],
        json={"assigned_to": str(setup["technician"].id)},
    )
    assert assigned.status_code == 200
    waiting = client.put(
        f"/api/v1/work-orders/{order['id']}/status",
        headers=setup["technician_headers"],
        json={"status": "AWAITING_PARTS"},
    )
    assert waiting.status_code == 409

    started = client.put(
        f"/api/v1/work-orders/{order['id']}/status",
        headers=setup["technician_headers"],
        json={"status": "IN_PROGRESS"},
    )
    assert started.status_code == 200
    waiting = client.put(
        f"/api/v1/work-orders/{order['id']}/status",
        headers=setup["technician_headers"],
        json={"status": "AWAITING_PARTS"},
    )
    assert waiting.status_code == 200
    assert waiting.json()["status"] == "AWAITING_PARTS"
    resumed = client.put(
        f"/api/v1/work-orders/{order['id']}/status",
        headers=setup["technician_headers"],
        json={"status": "IN_PROGRESS"},
    )
    assert resumed.status_code == 200

    degraded = _add_log(
        client,
        setup,
        order["id"],
        outcome="REPAIRED_DEGRADED",
    )
    assert degraded.status_code == 201, degraded.text
    cannot_close = client.put(
        f"/api/v1/work-orders/{order['id']}/close",
        headers=setup["manager_headers"],
        json={
            "confirmed": True,
            "verification_notes": "Instrument remains below the required performance.",
        },
    )
    assert cannot_close.status_code == 409

    rejected = client.put(
        f"/api/v1/work-orders/{order['id']}/close",
        headers=setup["manager_headers"],
        json={
            "confirmed": False,
            "verification_notes": "Repeat repair and test under full operating load.",
        },
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "IN_PROGRESS"
    assert rejected.json()["verification_notes"] == (
        "Repeat repair and test under full operating load."
    )
    assert len(rejected.json()["maintenance_logs"]) == 1
    assert [
        event["new_status"] for event in rejected.json()["status_history"]
    ] == [
        "OPEN",
        "ASSIGNED",
        "IN_PROGRESS",
        "AWAITING_PARTS",
        "IN_PROGRESS",
        "RESOLVED",
        "IN_PROGRESS",
    ]


def test_fault_scope_and_validation_are_enforced(client, test_engine) -> None:
    setup = _maintenance_setup(client, test_engine)
    auditor = insert_test_user(
        test_engine,
        email="auditor@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="AUDITOR",
    )
    auditor_headers = _headers(client, auditor)

    forbidden = _report(client, setup, headers=auditor_headers)
    assert forbidden.status_code == 403

    invalid = client.post(
        "/api/v1/work-orders",
        headers=setup["lab_tech_headers"],
        json={
            "asset_id": setup["asset"]["id"],
            "severity": "URGENT",
            "failure_category": "OPTICAL",
            "fault_description": " ",
        },
    )
    assert invalid.status_code == 422

    not_found = client.post(
        "/api/v1/work-orders",
        headers=setup["lab_tech_headers"],
        json=_report_payload(str(uuid.uuid4())),
    )
    assert not_found.status_code == 404

    response = _report(client, setup)
    order_id = response.json()["id"]
    unauthorized_assign = client.put(
        f"/api/v1/work-orders/{order_id}/assign",
        headers=setup["manager_headers"],
        json={"assigned_to": str(setup["technician"].id)},
    )
    assert unauthorized_assign.status_code == 403


def test_failed_repair_commit_rolls_back_order_and_log(
    client, test_engine, monkeypatch
) -> None:
    setup = _maintenance_setup(client, test_engine)
    order = _report(client, setup).json()
    _assign_and_start(client, setup, order)

    async def fail_commit(session, detail):
        raise HTTPException(status_code=503, detail="Simulated transaction failure")

    monkeypatch.setattr(maintenance_service, "_commit", fail_commit)
    response = _add_log(client, setup, order["id"])
    assert response.status_code == 503

    async def read_state():
        factory = async_sessionmaker(test_engine, expire_on_commit=False)
        async with factory() as session:
            saved_order = await session.get(WorkOrder, uuid.UUID(order["id"]))
            asset = await session.get(Asset, uuid.UUID(setup["asset"]["id"]))
            log_count = await session.scalar(
                select(func.count(MaintenanceLog.id)).where(
                    MaintenanceLog.work_order_id == uuid.UUID(order["id"])
                )
            )
            return saved_order.status, asset.operational_status, log_count

    status, asset_status, log_count = asyncio.run(read_state())
    assert status == "IN_PROGRESS"
    assert asset_status == "UNDER_MAINTENANCE"
    assert log_count == 0


def test_external_parts_approval_restores_previous_status_and_audits(
    client, test_engine, monkeypatch
) -> None:
    setup = _maintenance_setup(client, test_engine)
    monkeypatch.setattr(get_settings(), "maintenance_approver_roles", "ULMD_ADMIN")
    order = _report(client, setup).json()
    _assign_and_start(client, setup, order)
    request_url = (
        f"/api/v1/work-orders/{order['id']}/external-parts-approval"
    )

    requested = client.post(
        request_url,
        headers=setup["technician_headers"],
        json={"request_details": "Replacement lamp assembly required."},
    )
    assert requested.status_code == 200, requested.text
    requested_order = requested.json()
    assert requested_order["status"] == "AWAITING_APPROVAL"
    assert requested_order["external_parts_approval"]["decision"] == "PENDING"
    assert requested_order["external_parts_approval"]["request_details"] == (
        "Replacement lamp assembly required."
    )
    assert requested_order["approval_actions_configured"] is True
    assert requested_order["can_decide_external_parts_approval"] is False

    blocked = client.post(
        f"/api/v1/work-orders/{order['id']}/logs",
        headers=setup["technician_headers"],
        json={
            "actions_taken": "Attempted repair",
            "spare_parts_used": None,
            "labor_hours": "0.5",
            "outcome_condition": "OPERATIONAL",
        },
    )
    assert blocked.status_code == 409

    approved = client.put(
        f"/api/v1/work-orders/{order['id']}/external-parts-approval/decision",
        headers=setup["admin_headers"],
        json={"decision": "APPROVED", "decision_notes": "Approved for repair."},
    )
    assert approved.status_code == 200, approved.text
    approved_order = approved.json()
    assert approved_order["status"] == "IN_PROGRESS"
    assert approved_order["external_parts_approval"]["decision"] == "APPROVED"
    assert approved_order["external_parts_approval"]["decider_name"] == (
        setup["admin"].full_name
    )

    waiting = client.put(
        f"/api/v1/work-orders/{order['id']}/status",
        headers=setup["technician_headers"],
        json={"status": "AWAITING_PARTS"},
    )
    assert waiting.status_code == 200
    waiting_request = client.post(
        request_url,
        headers=setup["technician_headers"],
        json={"request_details": "External pump assembly is required."},
    )
    assert waiting_request.status_code == 200, waiting_request.text
    second_approval = client.put(
        f"/api/v1/work-orders/{order['id']}/external-parts-approval/decision",
        headers=setup["admin_headers"],
        json={"decision": "APPROVED", "decision_notes": None},
    )
    assert second_approval.status_code == 200, second_approval.text
    assert second_approval.json()["status"] == "AWAITING_PARTS"
    assert second_approval.json()["external_parts_approval"]["previous_status"] == (
        "AWAITING_PARTS"
    )

    async def read_approval_audit():
        factory = async_sessionmaker(test_engine, expire_on_commit=False)
        async with factory() as session:
            return list(
                (
                    await session.scalars(
                        select(AssetAuditLog)
                        .where(
                            AssetAuditLog.entity_type == "work_orders",
                            AssetAuditLog.entity_id == order["id"],
                            AssetAuditLog.action.in_(
                                [
                                    "EXTERNAL_PARTS_APPROVAL_REQUESTED",
                                    "EXTERNAL_PARTS_APPROVAL_APPROVED",
                                ]
                            ),
                        )
                        .order_by(AssetAuditLog.created_at, AssetAuditLog.id)
                    )
                ).all()
            )

    audit = asyncio.run(read_approval_audit())
    assert [entry.action for entry in audit] == [
        "EXTERNAL_PARTS_APPROVAL_REQUESTED",
        "EXTERNAL_PARTS_APPROVAL_APPROVED",
        "EXTERNAL_PARTS_APPROVAL_REQUESTED",
        "EXTERNAL_PARTS_APPROVAL_APPROVED",
    ]
    assert audit[0].new_values["external_parts_request_details"] == (
        "Replacement lamp assembly required."
    )
    assert approved_order["status_history"][-1]["action"] == (
        "EXTERNAL_PARTS_APPROVAL_APPROVED"
    )


def test_external_parts_approval_authorization_and_self_approval(
    client, test_engine, monkeypatch
) -> None:
    setup = _maintenance_setup(client, test_engine)
    monkeypatch.setattr(
        get_settings(), "maintenance_approver_roles", "MAINTENANCE_TECH"
    )
    order = _report(client, setup).json()
    _assign_and_start(client, setup, order)
    unauthorized_request = client.post(
        f"/api/v1/work-orders/{order['id']}/external-parts-approval",
        headers=setup["other_technician_headers"],
        json={"request_details": "Replacement power supply required."},
    )
    assert unauthorized_request.status_code == 403
    requested = client.post(
        f"/api/v1/work-orders/{order['id']}/external-parts-approval",
        headers=setup["technician_headers"],
        json={"request_details": "Replacement power supply required."},
    )
    assert requested.status_code == 200

    decision_url = (
        f"/api/v1/work-orders/{order['id']}/external-parts-approval/decision"
    )
    self_approval = client.put(
        decision_url,
        headers=setup["technician_headers"],
        json={"decision": "APPROVED"},
    )
    assert self_approval.status_code == 403

    unauthorized = client.put(
        decision_url,
        headers=setup["manager_headers"],
        json={"decision": "APPROVED"},
    )
    assert unauthorized.status_code == 403

    approved = client.put(
        decision_url,
        headers=setup["other_technician_headers"],
        json={"decision": "APPROVED"},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["external_parts_approval"]["decider_name"] == (
        setup["other_technician"].full_name
    )


def test_external_parts_rejection_is_audited_and_keeps_order_blocked(
    client, test_engine, monkeypatch
) -> None:
    setup = _maintenance_setup(client, test_engine)
    monkeypatch.setattr(get_settings(), "maintenance_approver_roles", "ULMD_ADMIN")
    order = _report(client, setup).json()
    _assign_and_start(client, setup, order)
    requested = client.post(
        f"/api/v1/work-orders/{order['id']}/external-parts-approval",
        headers=setup["technician_headers"],
        json={"request_details": "Replacement circuit board required."},
    )
    assert requested.status_code == 200

    rejected = client.put(
        f"/api/v1/work-orders/{order['id']}/external-parts-approval/decision",
        headers=setup["admin_headers"],
        json={"decision": "REJECTED", "decision_notes": "Request declined."},
    )
    assert rejected.status_code == 200, rejected.text
    rejected_order = rejected.json()
    assert rejected_order["status"] == "AWAITING_APPROVAL"
    assert rejected_order["external_parts_approval"]["decision"] == "REJECTED"
    assert rejected_order["external_parts_approval"]["decision_notes"] == (
        "Request declined."
    )
    assert rejected_order["status_history"][-1]["action"] == (
        "EXTERNAL_PARTS_APPROVAL_REJECTED"
    )
    assert rejected_order["status_history"][-1]["notes"] == "Request declined."

    cannot_resume = client.put(
        f"/api/v1/work-orders/{order['id']}/status",
        headers=setup["technician_headers"],
        json={"status": "IN_PROGRESS"},
    )
    assert cannot_resume.status_code == 409


def test_external_parts_decisions_disabled_without_configured_roles(
    client, test_engine, monkeypatch
) -> None:
    setup = _maintenance_setup(client, test_engine)
    monkeypatch.setattr(get_settings(), "maintenance_approver_roles", "")
    order = _report(client, setup).json()
    _assign_and_start(client, setup, order)
    requested = client.post(
        f"/api/v1/work-orders/{order['id']}/external-parts-approval",
        headers=setup["technician_headers"],
        json={"request_details": "Replacement sensor required."},
    )
    assert requested.status_code == 503
    unchanged = client.get(
        f"/api/v1/work-orders/{order['id']}",
        headers=setup["technician_headers"],
    )
    assert unchanged.status_code == 200
    assert unchanged.json()["status"] == "IN_PROGRESS"

    decision = client.put(
        f"/api/v1/work-orders/{order['id']}/external-parts-approval/decision",
        headers=setup["admin_headers"],
        json={"decision": "APPROVED"},
    )
    assert decision.status_code == 503
