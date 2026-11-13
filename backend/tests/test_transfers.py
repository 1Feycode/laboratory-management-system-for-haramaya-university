import asyncio
import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.security import hash_password
from app.models import Asset, AssetAuditLog, AssetTransfer
from app.services import transfer_service
from tests.conftest import insert_test_user


def _headers(client, user) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": "SecurePass123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _setup_transfer(client, test_engine):
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
    origin_manager = insert_test_user(
        test_engine,
        email="origin@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="LAB_MANAGER",
        department_id=department_id,
    )
    target_manager = insert_test_user(
        test_engine,
        email="target@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="LAB_MANAGER",
        department_id=department_id,
    )
    origin_headers = _headers(client, origin_manager)
    target_headers = _headers(client, target_manager)

    def create_lab(name: str, manager_id: uuid.UUID):
        laboratory = client.post(
            "/api/v1/hierarchy/laboratories",
            headers=admin_headers,
            json={
                "department_id": department["id"],
                "name": name,
                "lab_type": "WET",
                "manager_id": str(manager_id),
            },
        )
        assert laboratory.status_code == 201, laboratory.text
        room = client.post(
            "/api/v1/hierarchy/rooms",
            headers=admin_headers,
            json={
                "laboratory_id": laboratory.json()["id"],
                "room_number": "A-01",
                "building_name": "Central Laboratory Building",
            },
        )
        assert room.status_code == 201, room.text
        return laboratory.json(), room.json()

    origin, origin_room = create_lab("Origin Laboratory", origin_manager.id)
    target, target_room = create_lab("Destination Laboratory", target_manager.id)
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
            "serial_number": "SN-TRANSFER-01",
            "model_number": "UV-1900i",
            "manufacturer_name": "Shimadzu",
            "category_id": category.json()["id"],
            "laboratory_id": origin["id"],
            "room_id": origin_room["id"],
        },
    )
    assert asset.status_code == 201, asset.text
    return {
        "admin": admin,
        "admin_headers": admin_headers,
        "origin_manager": origin_manager,
        "origin_headers": origin_headers,
        "target_manager": target_manager,
        "target_headers": target_headers,
        "department": department,
        "origin": origin,
        "origin_room": origin_room,
        "target": target,
        "target_room": target_room,
        "asset": asset.json(),
    }


def _start_transfer(client, setup, *, headers=None, room_id=None):
    return client.post(
        "/api/v1/transfers",
        headers=headers or setup["origin_headers"],
        json={
            "asset_id": setup["asset"]["id"],
            "target_laboratory_id": setup["target"]["id"],
            "target_room_id": room_id or setup["target_room"]["id"],
            "transfer_reason": "Move the instrument to the destination laboratory",
        },
    )


def test_transfer_requires_dual_acceptance_and_preserves_location_history(
    client, test_engine
) -> None:
    setup = _setup_transfer(client, test_engine)

    created = _start_transfer(client, setup)
    assert created.status_code == 201, created.text
    transfer = created.json()
    assert transfer["status"] == "PENDING_RECEIVER"
    assert transfer["origin_room_id"] == setup["origin_room"]["id"]
    assert transfer["status_history"][0]["new_status"] == "PENDING_RECEIVER"

    locked_update = client.patch(
        f"/api/v1/assets/{setup['asset']['id']}",
        headers=setup["origin_headers"],
        json={"serial_number": "SN-CHANGED"},
    )
    assert locked_update.status_code == 409

    wrong_manager = client.put(
        f"/api/v1/transfers/{transfer['id']}/accept",
        headers=setup["origin_headers"],
        json={},
    )
    assert wrong_manager.status_code == 403

    accepted = client.put(
        f"/api/v1/transfers/{transfer['id']}/accept",
        headers=setup["target_headers"],
        json={"notes": "Instrument inspected on receipt"},
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "PENDING_ULMD"
    assert accepted.json()["accepted_by"] == str(setup["target_manager"].id)

    before_approval = client.get(
        f"/api/v1/assets/{setup['asset']['id']}",
        headers=setup["admin_headers"],
    ).json()
    assert before_approval["laboratory_id"] == setup["origin"]["id"]
    assert before_approval["operational_status"] == "TRANSFER_PENDING"

    completed = client.put(
        f"/api/v1/transfers/{transfer['id']}/approve",
        headers=setup["admin_headers"],
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "COMPLETED"
    assert completed.json()["approved_by_ulmd"] == str(setup["admin"].id)
    assert [event["new_status"] for event in completed.json()["status_history"]] == [
        "PENDING_RECEIVER",
        "PENDING_ULMD",
        "COMPLETED",
    ]

    updated_asset = client.get(
        f"/api/v1/assets/{setup['asset']['id']}",
        headers=setup["admin_headers"],
    ).json()
    assert updated_asset["laboratory_id"] == setup["target"]["id"]
    assert updated_asset["room_id"] == setup["target_room"]["id"]
    assert updated_asset["operational_status"] == "OPERATIONAL"

    room_reassignment = client.patch(
        f"/api/v1/hierarchy/rooms/{setup['origin_room']['id']}",
        headers=setup["admin_headers"],
        json={"laboratory_id": setup["target"]["id"]},
    )
    assert room_reassignment.status_code == 409

    async def read_audit_records():
        factory = async_sessionmaker(test_engine, expire_on_commit=False)
        async with factory() as session:
            transfer_logs = list(
                (
                    await session.scalars(
                        select(AssetAuditLog).where(
                            AssetAuditLog.entity_type == "asset_transfers",
                            AssetAuditLog.entity_id == transfer["id"],
                        ).order_by(AssetAuditLog.id)
                    )
                ).all()
            )
            asset_logs = list(
                (
                    await session.scalars(
                        select(AssetAuditLog).where(
                            AssetAuditLog.entity_id == setup["asset"]["id"],
                            AssetAuditLog.action.in_(
                                [
                                    "ASSET_TRANSFER_PENDING",
                                    "ASSET_TRANSFER_COMPLETED",
                                ]
                            ),
                        ).order_by(AssetAuditLog.id)
                    )
                ).all()
            )
            return transfer_logs, asset_logs

    transfer_logs, asset_logs = asyncio.run(read_audit_records())
    assert [log.action for log in transfer_logs] == [
        "TRANSFER_INITIATED",
        "TRANSFER_ACCEPTED",
        "TRANSFER_COMPLETED",
    ]
    assert len(asset_logs) == 2
    assert asset_logs[0].old_values["laboratory_id"] == setup["origin"]["id"]
    assert asset_logs[-1].new_values["laboratory_id"] == setup["target"]["id"]


def test_transfer_rejects_invalid_scope_and_restores_asset(
    client, test_engine
) -> None:
    setup = _setup_transfer(client, test_engine)
    third_manager = insert_test_user(
        test_engine,
        email="outsider@example.edu",
        password_hash=hash_password("SecurePass123"),
        role_name="LAB_MANAGER",
        department_id=uuid.UUID(setup["department"]["id"]),
    )
    third_headers = _headers(client, third_manager)

    invalid_room = client.post(
        "/api/v1/hierarchy/rooms",
        headers=setup["admin_headers"],
        json={
            "laboratory_id": setup["origin"]["id"],
            "room_number": "A-02",
            "building_name": "Central Laboratory Building",
        },
    )
    assert invalid_room.status_code == 201
    invalid_destination = _start_transfer(
        client,
        setup,
        room_id=invalid_room.json()["id"],
    )
    assert invalid_destination.status_code == 422

    started = _start_transfer(client, setup)
    assert started.status_code == 201, started.text
    transfer = started.json()
    unauthorized_accept = client.put(
        f"/api/v1/transfers/{transfer['id']}/accept",
        headers=third_headers,
        json={},
    )
    assert unauthorized_accept.status_code == 403

    rejection = client.put(
        f"/api/v1/transfers/{transfer['id']}/reject",
        headers=setup["target_headers"],
        json={"notes": "Destination is not ready to receive this instrument"},
    )
    assert rejection.status_code == 200, rejection.text
    assert rejection.json()["status"] == "REJECTED"
    assert rejection.json()["notes"] == "Destination is not ready to receive this instrument"
    assert rejection.json()["status_history"][-1]["new_status"] == "REJECTED"

    asset = client.get(
        f"/api/v1/assets/{setup['asset']['id']}",
        headers=setup["admin_headers"],
    ).json()
    assert asset["laboratory_id"] == setup["origin"]["id"]
    assert asset["room_id"] == setup["origin_room"]["id"]
    assert asset["operational_status"] == "OPERATIONAL"


def test_ulmd_can_reject_after_receiver_acceptance(client, test_engine) -> None:
    setup = _setup_transfer(client, test_engine)
    started = _start_transfer(client, setup)
    assert started.status_code == 201, started.text
    transfer_id = started.json()["id"]

    accepted = client.put(
        f"/api/v1/transfers/{transfer_id}/accept",
        headers=setup["target_headers"],
        json={},
    )
    assert accepted.status_code == 200, accepted.text

    manager_rejection = client.put(
        f"/api/v1/transfers/{transfer_id}/reject",
        headers=setup["target_headers"],
        json={"notes": "A pending ULMD decision cannot be rejected by a manager"},
    )
    assert manager_rejection.status_code == 403

    rejection = client.put(
        f"/api/v1/transfers/{transfer_id}/reject",
        headers=setup["admin_headers"],
        json={"notes": "Relocation is not approved"},
    )
    assert rejection.status_code == 200, rejection.text
    assert rejection.json()["status"] == "REJECTED"
    assert rejection.json()["status_history"][-1]["new_status"] == "REJECTED"

    asset = client.get(
        f"/api/v1/assets/{setup['asset']['id']}",
        headers=setup["admin_headers"],
    ).json()
    assert asset["laboratory_id"] == setup["origin"]["id"]
    assert asset["room_id"] == setup["origin_room"]["id"]
    assert asset["operational_status"] == "OPERATIONAL"


def test_non_operational_asset_cannot_start_transfer(client, test_engine) -> None:
    setup = _setup_transfer(client, test_engine)

    async def mark_defective():
        factory = async_sessionmaker(test_engine, expire_on_commit=False)
        async with factory() as session:
            asset = await session.get(Asset, uuid.UUID(setup["asset"]["id"]))
            asset.operational_status = "DEFECTIVE"
            await session.commit()

    asyncio.run(mark_defective())
    response = _start_transfer(client, setup)
    assert response.status_code == 409


def test_failed_final_commit_rolls_back_transfer_and_location(
    client, test_engine, monkeypatch
) -> None:
    setup = _setup_transfer(client, test_engine)
    started = _start_transfer(client, setup)
    assert started.status_code == 201, started.text
    transfer_id = started.json()["id"]
    accepted = client.put(
        f"/api/v1/transfers/{transfer_id}/accept",
        headers=setup["target_headers"],
        json={},
    )
    assert accepted.status_code == 200, accepted.text

    async def fail_commit(session, detail):
        raise HTTPException(status_code=503, detail="Simulated transaction failure")

    monkeypatch.setattr(transfer_service, "_commit", fail_commit)
    response = client.put(
        f"/api/v1/transfers/{transfer_id}/approve",
        headers=setup["admin_headers"],
    )
    assert response.status_code == 503

    async def read_state():
        factory = async_sessionmaker(test_engine, expire_on_commit=False)
        async with factory() as session:
            transfer = await session.get(AssetTransfer, uuid.UUID(transfer_id))
            asset = await session.get(Asset, uuid.UUID(setup["asset"]["id"]))
            return transfer.status, asset.laboratory_id, asset.operational_status

    transfer_status, laboratory_id, asset_status = asyncio.run(read_state())
    assert transfer_status == "PENDING_ULMD"
    assert str(laboratory_id) == setup["origin"]["id"]
    assert asset_status == "TRANSFER_PENDING"
