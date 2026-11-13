import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import HTTPException
from sqlalchemy import desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.asset import Asset, AssetAuditLog
from app.models.asset_transfer import AssetTransfer
from app.models.organization import Laboratory, Room
from app.models.user import User
from app.schemas.transfer import (
    TransferAcceptance,
    TransferCreate,
    TransferPage,
    TransferRead,
    TransferRejection,
    TransferStatus,
    TransferStatusEvent,
)

logger = logging.getLogger(__name__)
TransferEventAction = Literal[
    "TRANSFER_INITIATED",
    "TRANSFER_ACCEPTED",
    "TRANSFER_REJECTED",
    "TRANSFER_COMPLETED",
]


async def _commit(session: AsyncSession, detail: str) -> None:
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail=detail) from None


def _transfer_query():
    return select(AssetTransfer).options(
        joinedload(AssetTransfer.asset),
        joinedload(AssetTransfer.origin_laboratory).joinedload(
            Laboratory.department
        ),
        joinedload(AssetTransfer.origin_room),
        joinedload(AssetTransfer.target_laboratory).joinedload(
            Laboratory.department
        ),
        joinedload(AssetTransfer.target_room),
        joinedload(AssetTransfer.initiator),
        joinedload(AssetTransfer.accepter),
        joinedload(AssetTransfer.ulmd_approver),
    )


def _transfer_values(transfer: AssetTransfer) -> dict[str, object]:
    return {
        "asset_id": str(transfer.asset_id),
        "origin_laboratory_id": str(transfer.origin_laboratory_id),
        "origin_room_id": str(transfer.origin_room_id),
        "target_laboratory_id": str(transfer.target_laboratory_id),
        "target_room_id": str(transfer.target_room_id),
        "initiated_by": str(transfer.initiated_by),
        "accepted_by": str(transfer.accepted_by) if transfer.accepted_by else None,
        "approved_by_ulmd": (
            str(transfer.approved_by_ulmd) if transfer.approved_by_ulmd else None
        ),
        "status": transfer.status,
        "transfer_reason": transfer.transfer_reason,
        "notes": transfer.notes,
        "created_at": transfer.created_at.isoformat() if transfer.created_at else None,
        "completed_at": (
            transfer.completed_at.isoformat() if transfer.completed_at else None
        ),
    }


def _asset_location_values(asset: Asset) -> dict[str, str]:
    return {
        "asset_code": asset.asset_code,
        "laboratory_id": str(asset.laboratory_id),
        "room_id": str(asset.room_id),
        "operational_status": asset.operational_status,
    }


def _audit_transfer(
    transfer: AssetTransfer,
    user: User,
    action: TransferEventAction,
    old_values: dict[str, object] | None,
    ip_address: str | None,
) -> AssetAuditLog:
    return AssetAuditLog(
        user_id=user.id,
        action=action,
        entity_type="asset_transfers",
        entity_id=str(transfer.id),
        old_values=old_values,
        new_values=_transfer_values(transfer),
        ip_address=ip_address,
    )


def _audit_asset(
    asset: Asset,
    transfer: AssetTransfer,
    user: User,
    action: str,
    old_values: dict[str, str],
    ip_address: str | None,
) -> AssetAuditLog:
    values = _asset_location_values(asset)
    values["transfer_id"] = str(transfer.id)
    return AssetAuditLog(
        user_id=user.id,
        action=action,
        entity_type="assets",
        entity_id=str(asset.id),
        old_values=old_values,
        new_values=values,
        ip_address=ip_address,
    )


async def _status_history(
    session: AsyncSession, transfer_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[TransferStatusEvent]]:
    history = {transfer_id: [] for transfer_id in transfer_ids}
    if not transfer_ids:
        return history
    records = await session.execute(
        select(AssetAuditLog, User.full_name)
        .outerjoin(User, AssetAuditLog.user_id == User.id)
        .where(
            AssetAuditLog.entity_type == "asset_transfers",
            AssetAuditLog.entity_id.in_([str(value) for value in transfer_ids]),
        )
        .order_by(AssetAuditLog.created_at, AssetAuditLog.id)
    )
    for record, actor_name in records:
        transfer_id = uuid.UUID(record.entity_id)
        old_values = record.old_values or {}
        new_values = record.new_values or {}
        history[transfer_id].append(
            TransferStatusEvent(
                action=record.action,
                actor_id=record.user_id,
                actor_name=actor_name,
                old_status=old_values.get("status"),
                new_status=new_values["status"],
                notes=new_values.get("notes"),
                occurred_at=record.created_at,
            )
        )
    return history


def _transfer_read(
    transfer: AssetTransfer, status_history: list[TransferStatusEvent]
) -> TransferRead:
    return TransferRead(
        id=transfer.id,
        asset_id=transfer.asset_id,
        asset_code=transfer.asset.asset_code,
        origin_laboratory_id=transfer.origin_laboratory_id,
        origin_laboratory_name=transfer.origin_laboratory.name,
        origin_room_id=transfer.origin_room_id,
        origin_room_number=transfer.origin_room.room_number,
        origin_building_name=transfer.origin_room.building_name,
        target_laboratory_id=transfer.target_laboratory_id,
        target_laboratory_name=transfer.target_laboratory.name,
        target_room_id=transfer.target_room_id,
        target_room_number=transfer.target_room.room_number,
        target_building_name=transfer.target_room.building_name,
        initiated_by=transfer.initiated_by,
        initiator_name=transfer.initiator.full_name,
        accepted_by=transfer.accepted_by,
        accepter_name=transfer.accepter.full_name if transfer.accepter else None,
        approved_by_ulmd=transfer.approved_by_ulmd,
        approver_name=(
            transfer.ulmd_approver.full_name if transfer.ulmd_approver else None
        ),
        status=transfer.status,
        transfer_reason=transfer.transfer_reason,
        notes=transfer.notes,
        created_at=transfer.created_at,
        completed_at=transfer.completed_at,
        status_history=status_history,
    )


async def _get_transfer_record(
    session: AsyncSession, transfer_id: uuid.UUID
) -> AssetTransfer:
    transfer = await session.scalar(
        _transfer_query().where(AssetTransfer.id == transfer_id)
    )
    if transfer is None:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return transfer


async def get_transfer(
    session: AsyncSession, transfer_id: uuid.UUID, user: User | None = None
) -> TransferRead:
    transfer = await _get_transfer_record(session, transfer_id)
    if user is not None:
        _ensure_transfer_visible(user, transfer)
    history = await _status_history(session, [transfer.id])
    return _transfer_read(transfer, history[transfer.id])


def _ensure_transfer_visible(user: User, transfer: AssetTransfer) -> None:
    if user.role.name in {"ULMD_ADMIN", "AUDITOR"}:
        return
    if user.role.name == "LAB_MANAGER" and user.id in {
        transfer.origin_laboratory.manager_id,
        transfer.target_laboratory.manager_id,
    }:
        return
    raise HTTPException(
        status_code=403, detail="You cannot view transfers outside your assigned role scope"
    )


async def list_transfers(
    session: AsyncSession,
    *,
    page: int,
    size: int,
    status_filter: TransferStatus | None,
    asset_id: uuid.UUID | None,
    user: User,
) -> TransferPage:
    filters = []
    if status_filter:
        filters.append(AssetTransfer.status == status_filter)
    if asset_id:
        filters.append(AssetTransfer.asset_id == asset_id)
    if user.role.name == "LAB_MANAGER":
        managed_laboratories = select(Laboratory.id).where(
            Laboratory.manager_id == user.id
        )
        filters.append(
            or_(
                AssetTransfer.origin_laboratory_id.in_(managed_laboratories),
                AssetTransfer.target_laboratory_id.in_(managed_laboratories),
            )
        )
    total = await session.scalar(
        select(func.count(AssetTransfer.id)).where(*filters)
    ) or 0
    records = list(
        (
            await session.scalars(
                _transfer_query()
                .where(*filters)
                .order_by(desc(AssetTransfer.created_at), AssetTransfer.id)
                .offset((page - 1) * size)
                .limit(size)
            )
        ).all()
    )
    histories = await _status_history(
        session, [record.id for record in records]
    )
    for record in records:
        _ensure_transfer_visible(user, record)
    return TransferPage(
        items=[
            _transfer_read(record, histories[record.id]) for record in records
        ],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


def _authorize_laboratory_action(user: User, laboratory: Laboratory) -> None:
    if user.role.name == "ULMD_ADMIN":
        return
    if user.role.name != "LAB_MANAGER":
        raise HTTPException(
            status_code=403, detail="Only a laboratory manager can perform this action"
        )
    if user.department_id != laboratory.department_id:
        raise HTTPException(
            status_code=403, detail="You cannot act outside your assigned department"
        )
    if laboratory.manager_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not the designated manager of this laboratory",
        )


async def _load_laboratory(
    session: AsyncSession, laboratory_id: uuid.UUID
) -> Laboratory:
    laboratory = await session.scalar(
        select(Laboratory)
        .options(joinedload(Laboratory.manager).joinedload(User.role))
        .where(Laboratory.id == laboratory_id)
        .with_for_update(of=Laboratory)
    )
    if laboratory is None:
        raise HTTPException(status_code=422, detail="Laboratory does not exist")
    return laboratory


async def _load_room(
    session: AsyncSession, room_id: uuid.UUID
) -> Room:
    room = await session.scalar(
        select(Room).where(Room.id == room_id).with_for_update()
    )
    if room is None:
        raise HTTPException(status_code=422, detail="Room does not exist")
    return room


def _validate_destination_manager(laboratory: Laboratory) -> None:
    manager = laboratory.manager
    if (
        manager is None
        or not manager.is_active
        or manager.department_id != laboratory.department_id
        or manager.role.name != "LAB_MANAGER"
    ):
        raise HTTPException(
            status_code=409,
            detail="Destination laboratory must have an active designated Lab Manager",
        )


def _validate_asset_source(asset: Asset, transfer: AssetTransfer) -> None:
    if (
        asset.operational_status != "TRANSFER_PENDING"
        or asset.laboratory_id != transfer.origin_laboratory_id
        or asset.room_id != transfer.origin_room_id
    ):
        raise HTTPException(
            status_code=409,
            detail="Asset state or location no longer matches the pending transfer",
        )


async def create_transfer(
    session: AsyncSession,
    payload: TransferCreate,
    user: User,
    ip_address: str | None,
) -> TransferRead:
    asset = await session.scalar(
        select(Asset)
        .where(Asset.id == payload.asset_id)
        .with_for_update()
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    if asset.operational_status != "OPERATIONAL":
        raise HTTPException(
            status_code=409,
            detail="Only OPERATIONAL assets can be transferred",
        )
    if asset.room_id == payload.target_room_id:
        raise HTTPException(
            status_code=422,
            detail="The destination room must differ from the current room",
        )

    origin_laboratory = await _load_laboratory(session, asset.laboratory_id)
    if user.role.name != "ULMD_ADMIN":
        _authorize_laboratory_action(user, origin_laboratory)
    origin_room = await _load_room(session, asset.room_id)
    if origin_room.laboratory_id != origin_laboratory.id:
        raise HTTPException(
            status_code=409,
            detail="Asset room no longer belongs to its current laboratory",
        )

    target_laboratory = await _load_laboratory(
        session, payload.target_laboratory_id
    )
    _validate_destination_manager(target_laboratory)
    target_room = await _load_room(session, payload.target_room_id)
    if target_room.laboratory_id != target_laboratory.id:
        raise HTTPException(
            status_code=422,
            detail="Destination room must belong to the destination laboratory",
        )

    old_asset_values = _asset_location_values(asset)
    transfer = AssetTransfer(
        asset_id=asset.id,
        origin_laboratory_id=asset.laboratory_id,
        origin_room_id=asset.room_id,
        target_laboratory_id=target_laboratory.id,
        target_room_id=target_room.id,
        initiated_by=user.id,
        status="PENDING_RECEIVER",
        transfer_reason=payload.transfer_reason,
    )
    asset.operational_status = "TRANSFER_PENDING"
    asset.updated_at = datetime.now(timezone.utc)
    session.add(transfer)
    await session.flush()
    session.add_all(
        [
            _audit_transfer(transfer, user, "TRANSFER_INITIATED", None, ip_address),
            _audit_asset(
                asset,
                transfer,
                user,
                "ASSET_TRANSFER_PENDING",
                old_asset_values,
                ip_address,
            ),
        ]
    )
    await _commit(session, "Transfer could not be created")
    logger.info(
        "transfers.initiated",
        extra={"transfer_id": str(transfer.id), "asset_id": str(asset.id)},
    )
    return await get_transfer(session, transfer.id, user)


async def accept_transfer(
    session: AsyncSession,
    transfer_id: uuid.UUID,
    payload: TransferAcceptance,
    user: User,
    ip_address: str | None,
) -> TransferRead:
    transfer = await session.scalar(
        select(AssetTransfer)
        .where(AssetTransfer.id == transfer_id)
        .with_for_update()
    )
    if transfer is None:
        raise HTTPException(status_code=404, detail="Transfer not found")
    if transfer.status != "PENDING_RECEIVER":
        raise HTTPException(
            status_code=409, detail="Transfer is not awaiting receiver acceptance"
        )
    target_laboratory = await _load_laboratory(
        session, transfer.target_laboratory_id
    )
    _authorize_laboratory_action(user, target_laboratory)
    asset = await session.scalar(
        select(Asset).where(Asset.id == transfer.asset_id).with_for_update()
    )
    if asset is None:
        raise HTTPException(status_code=409, detail="Transfer asset no longer exists")
    _validate_asset_source(asset, transfer)

    old_values = _transfer_values(transfer)
    transfer.status = "PENDING_ULMD"
    transfer.accepted_by = user.id
    if payload.notes is not None:
        transfer.notes = payload.notes
    session.add(
        _audit_transfer(
            transfer, user, "TRANSFER_ACCEPTED", old_values, ip_address
        )
    )
    await _commit(session, "Transfer acceptance could not be saved")
    logger.info("transfers.accepted", extra={"transfer_id": str(transfer.id)})
    return await get_transfer(session, transfer.id, user)


async def reject_transfer(
    session: AsyncSession,
    transfer_id: uuid.UUID,
    payload: TransferRejection,
    user: User,
    ip_address: str | None,
) -> TransferRead:
    transfer = await session.scalar(
        select(AssetTransfer)
        .where(AssetTransfer.id == transfer_id)
        .with_for_update()
    )
    if transfer is None:
        raise HTTPException(status_code=404, detail="Transfer not found")
    if transfer.status == "PENDING_RECEIVER":
        target_laboratory = await _load_laboratory(
            session, transfer.target_laboratory_id
        )
        _authorize_laboratory_action(user, target_laboratory)
    elif transfer.status == "PENDING_ULMD":
        if user.role.name != "ULMD_ADMIN":
            raise HTTPException(
                status_code=403,
                detail="Only ULMD_ADMIN can reject a transfer awaiting final approval",
            )
    else:
        raise HTTPException(
            status_code=409, detail="Only an active transfer can be rejected"
        )

    asset = await session.scalar(
        select(Asset).where(Asset.id == transfer.asset_id).with_for_update()
    )
    if asset is None:
        raise HTTPException(status_code=409, detail="Transfer asset no longer exists")
    _validate_asset_source(asset, transfer)
    old_transfer_values = _transfer_values(transfer)
    old_asset_values = _asset_location_values(asset)
    transfer.status = "REJECTED"
    transfer.notes = payload.notes
    asset.operational_status = "OPERATIONAL"
    asset.updated_at = datetime.now(timezone.utc)
    session.add_all(
        [
            _audit_transfer(
                transfer,
                user,
                "TRANSFER_REJECTED",
                old_transfer_values,
                ip_address,
            ),
            _audit_asset(
                asset,
                transfer,
                user,
                "ASSET_TRANSFER_RESTORED",
                old_asset_values,
                ip_address,
            ),
        ]
    )
    await _commit(session, "Transfer rejection could not be saved")
    logger.info("transfers.rejected", extra={"transfer_id": str(transfer.id)})
    return await get_transfer(session, transfer.id, user)


async def approve_transfer(
    session: AsyncSession,
    transfer_id: uuid.UUID,
    user: User,
    ip_address: str | None,
) -> TransferRead:
    transfer = await session.scalar(
        select(AssetTransfer)
        .where(AssetTransfer.id == transfer_id)
        .with_for_update()
    )
    if transfer is None:
        raise HTTPException(status_code=404, detail="Transfer not found")
    if transfer.status != "PENDING_ULMD":
        raise HTTPException(
            status_code=409, detail="Transfer is not awaiting ULMD approval"
        )
    asset = await session.scalar(
        select(Asset).where(Asset.id == transfer.asset_id).with_for_update()
    )
    if asset is None:
        raise HTTPException(status_code=409, detail="Transfer asset no longer exists")
    _validate_asset_source(asset, transfer)

    target_laboratory = await _load_laboratory(
        session, transfer.target_laboratory_id
    )
    target_room = await _load_room(session, transfer.target_room_id)
    if target_room.laboratory_id != target_laboratory.id:
        raise HTTPException(
            status_code=409,
            detail="Destination room no longer belongs to the destination laboratory",
        )

    old_transfer_values = _transfer_values(transfer)
    old_asset_values = _asset_location_values(asset)
    asset.laboratory_id = target_laboratory.id
    asset.room_id = target_room.id
    asset.operational_status = "OPERATIONAL"
    asset.updated_at = datetime.now(timezone.utc)
    transfer.status = "COMPLETED"
    transfer.approved_by_ulmd = user.id
    transfer.completed_at = datetime.now(timezone.utc)
    session.add_all(
        [
            _audit_transfer(
                transfer,
                user,
                "TRANSFER_COMPLETED",
                old_transfer_values,
                ip_address,
            ),
            _audit_asset(
                asset,
                transfer,
                user,
                "ASSET_TRANSFER_COMPLETED",
                old_asset_values,
                ip_address,
            ),
        ]
    )
    await _commit(session, "Transfer approval could not be saved")
    logger.info("transfers.completed", extra={"transfer_id": str(transfer.id)})
    return await get_transfer(session, transfer.id, user)
