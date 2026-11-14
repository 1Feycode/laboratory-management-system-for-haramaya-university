import logging
import math
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from fastapi import HTTPException
from sqlalchemy import Integer, and_, case, desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.config import get_settings
from app.models.asset import Asset, AssetAuditLog
from app.models.maintenance import MaintenanceLog, WorkOrder
from app.models.organization import Laboratory
from app.models.user import User
from app.schemas.maintenance import (
    FaultReportCreate,
    ExternalPartsApprovalDecisionUpdate,
    ExternalPartsApprovalRead,
    ExternalPartsApprovalRequest,
    MaintenanceLogCreate,
    MaintenanceLogRead,
    MaintenancePage,
    MaintenanceVerification,
    WorkOrderRead,
    WorkOrderSeverity,
    WorkOrderStatus,
    WorkOrderStatusEvent,
    WorkOrderStatusUpdate,
)

logger = logging.getLogger(__name__)
AuditAction = Literal[
    "WORK_ORDER_CREATED",
    "WORK_ORDER_ASSIGNED",
    "WORK_ORDER_STARTED",
    "WORK_ORDER_STATUS_CHANGED",
    "MAINTENANCE_LOG_ADDED",
    "WORK_ORDER_REPAIR_REJECTED",
    "WORK_ORDER_CLOSED",
    "EXTERNAL_PARTS_APPROVAL_REQUESTED",
    "EXTERNAL_PARTS_APPROVAL_APPROVED",
    "EXTERNAL_PARTS_APPROVAL_REJECTED",
]


async def _commit(session: AsyncSession, detail: str) -> None:
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail=detail) from None


def _work_order_query():
    return (
        select(WorkOrder)
        .options(
            joinedload(WorkOrder.asset).joinedload(Asset.laboratory),
            joinedload(WorkOrder.reporter),
            joinedload(WorkOrder.assignee),
            joinedload(WorkOrder.verifier),
            joinedload(WorkOrder.external_parts_requester),
            joinedload(WorkOrder.external_parts_decider),
            selectinload(WorkOrder.logs).joinedload(MaintenanceLog.technician),
        )
    )


def _work_order_values(order: WorkOrder) -> dict[str, object]:
    return {
        "ticket_number": order.ticket_number,
        "asset_id": str(order.asset_id),
        "reported_by": str(order.reported_by),
        "assigned_to": str(order.assigned_to) if order.assigned_to else None,
        "severity": order.severity,
        "failure_category": order.failure_category,
        "status": order.status,
        "fault_description": order.fault_description,
        "verified_by": str(order.verified_by) if order.verified_by else None,
        "verification_notes": order.verification_notes,
        "external_parts_request_details": order.external_parts_request_details,
        "external_parts_requested_by": (
            str(order.external_parts_requested_by)
            if order.external_parts_requested_by
            else None
        ),
        "external_parts_requested_at": (
            order.external_parts_requested_at.isoformat()
            if order.external_parts_requested_at
            else None
        ),
        "external_parts_previous_status": order.external_parts_previous_status,
        "external_parts_decision": order.external_parts_decision,
        "external_parts_decided_by": (
            str(order.external_parts_decided_by)
            if order.external_parts_decided_by
            else None
        ),
        "external_parts_decided_at": (
            order.external_parts_decided_at.isoformat()
            if order.external_parts_decided_at
            else None
        ),
        "external_parts_decision_notes": order.external_parts_decision_notes,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "resolved_at": order.resolved_at.isoformat() if order.resolved_at else None,
        "closed_at": order.closed_at.isoformat() if order.closed_at else None,
    }


def _asset_values(asset: Asset) -> dict[str, str]:
    return {
        "asset_code": asset.asset_code,
        "operational_status": asset.operational_status,
        "laboratory_id": str(asset.laboratory_id),
        "room_id": str(asset.room_id),
    }


def _audit(
    *,
    user: User,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    old_values: dict[str, object] | None,
    new_values: dict[str, object] | None,
    ip_address: str | None,
) -> AssetAuditLog:
    return AssetAuditLog(
        user_id=user.id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
    )


def _order_read(
    order: WorkOrder, history: list[WorkOrderStatusEvent], user: User
) -> WorkOrderRead:
    settings = get_settings()
    approval_roles = settings.maintenance_approval_role_names
    approval = None
    if (
        order.external_parts_request_details is not None
        and order.external_parts_requested_by is not None
        and order.external_parts_requested_at is not None
        and order.external_parts_previous_status is not None
        and order.external_parts_decision is not None
    ):
        approval = ExternalPartsApprovalRead(
            request_details=order.external_parts_request_details,
            requested_by=order.external_parts_requested_by,
            requester_name=order.external_parts_requester.full_name,
            requested_at=order.external_parts_requested_at,
            previous_status=order.external_parts_previous_status,
            decision=order.external_parts_decision,
            decided_by=order.external_parts_decided_by,
            decider_name=(
                order.external_parts_decider.full_name
                if order.external_parts_decider
                else None
            ),
            decided_at=order.external_parts_decided_at,
            decision_notes=order.external_parts_decision_notes,
        )
    return WorkOrderRead(
        id=order.id,
        ticket_number=order.ticket_number,
        asset_id=order.asset_id,
        asset_code=order.asset.asset_code,
        asset_model_number=order.asset.model_number,
        asset_manufacturer_name=order.asset.manufacturer_name,
        laboratory_id=order.asset.laboratory_id,
        laboratory_name=order.asset.laboratory.name,
        reported_by=order.reported_by,
        reporter_name=order.reporter.full_name,
        assigned_to=order.assigned_to,
        assignee_name=order.assignee.full_name if order.assignee else None,
        severity=order.severity,
        failure_category=order.failure_category,
        status=order.status,
        fault_description=order.fault_description,
        verified_by=order.verified_by,
        verifier_name=order.verifier.full_name if order.verifier else None,
        verification_notes=order.verification_notes,
        created_at=order.created_at,
        resolved_at=order.resolved_at,
        closed_at=order.closed_at,
        external_parts_approval=approval,
        approval_actions_configured=bool(approval_roles),
        can_decide_external_parts_approval=(
            bool(approval_roles)
            and user.role.name in approval_roles
            and user.id != order.external_parts_requested_by
        ),
        maintenance_logs=[
            MaintenanceLogRead(
                id=log.id,
                work_order_id=log.work_order_id,
                technician_id=log.technician_id,
                technician_name=log.technician.full_name,
                actions_taken=log.actions_taken,
                spare_parts_used=log.spare_parts_used,
                labor_hours=log.labor_hours,
                outcome_condition=log.outcome_condition,
                created_at=log.created_at,
            )
            for log in order.logs
        ],
        status_history=history,
    )


async def _status_history(
    session: AsyncSession, order_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[WorkOrderStatusEvent]]:
    history = {order_id: [] for order_id in order_ids}
    if not order_ids:
        return history
    records = await session.execute(
        select(AssetAuditLog, User.full_name)
        .outerjoin(User, AssetAuditLog.user_id == User.id)
        .where(
            AssetAuditLog.entity_type == "work_orders",
            AssetAuditLog.entity_id.in_([str(value) for value in order_ids]),
        )
        .order_by(AssetAuditLog.created_at, AssetAuditLog.id)
    )
    for record, actor_name in records:
        order_id = uuid.UUID(record.entity_id)
        old_values = record.old_values or {}
        new_values = record.new_values or {}
        history[order_id].append(
            WorkOrderStatusEvent(
                action=record.action,
                actor_id=record.user_id,
                actor_name=actor_name,
                old_status=old_values.get("status"),
                new_status=new_values["status"],
                old_assignee_id=old_values.get("assigned_to"),
                new_assignee_id=new_values.get("assigned_to"),
                notes=(
                    new_values.get("verification_notes")
                    or new_values.get("external_parts_decision_notes")
                ),
                external_parts_request_details=new_values.get(
                    "external_parts_request_details"
                ),
                external_parts_decision=new_values.get("external_parts_decision"),
                occurred_at=record.created_at,
            )
        )
    return history


def _ensure_report_access(user: User, asset: Asset) -> None:
    if user.role.name == "ULMD_ADMIN":
        return
    laboratory = asset.laboratory
    if user.role.name == "LAB_MANAGER":
        allowed = (
            laboratory.manager_id == user.id
            and laboratory.department_id == user.department_id
        )
    elif user.role.name == "LAB_TECH":
        allowed = laboratory.department_id == user.department_id
    else:
        allowed = False
    if not allowed:
        raise HTTPException(
            status_code=403,
            detail="You cannot report faults for assets outside your assigned scope",
        )


def _ensure_read_access(user: User, order: WorkOrder) -> None:
    role = user.role.name
    if role in {"ULMD_ADMIN", "AUDITOR"}:
        return
    if (
        order.external_parts_requested_by is not None
        and user.id != order.external_parts_requested_by
        and role in get_settings().maintenance_approval_role_names
    ):
        return
    if role == "MAINTENANCE_TECH" and order.assigned_to == user.id:
        return
    laboratory = order.asset.laboratory
    if (
        role == "LAB_MANAGER"
        and laboratory.manager_id == user.id
        and laboratory.department_id == user.department_id
    ):
        return
    if (
        role == "LAB_TECH"
        and user.department_id is not None
        and laboratory.department_id == user.department_id
    ):
        return
    raise HTTPException(
        status_code=403,
        detail="You cannot view work orders outside your assigned scope",
    )


async def _get_order_record(
    session: AsyncSession, order_id: uuid.UUID, *, lock: bool = False
) -> WorkOrder:
    statement = select(WorkOrder).where(WorkOrder.id == order_id)
    if lock:
        statement = statement.with_for_update()
    order = await session.scalar(statement)
    if order is None:
        raise HTTPException(status_code=404, detail="Work order not found")
    return order


async def _load_order(session: AsyncSession, order_id: uuid.UUID) -> WorkOrder:
    order = await session.scalar(
        _work_order_query().where(WorkOrder.id == order_id)
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Work order not found")
    return order


async def _read_order(
    session: AsyncSession, order_id: uuid.UUID, user: User
) -> WorkOrderRead:
    order = await _load_order(session, order_id)
    _ensure_read_access(user, order)
    history = await _status_history(session, [order.id])
    return _order_read(order, history[order.id], user)


async def list_work_orders(
    session: AsyncSession,
    *,
    page: int,
    size: int,
    status_filter: WorkOrderStatus | None,
    severity_filter: WorkOrderSeverity | None,
    asset_id: uuid.UUID | None,
    user: User,
) -> MaintenancePage[WorkOrderRead]:
    filters = []
    if status_filter:
        filters.append(WorkOrder.status == status_filter)
    if severity_filter:
        filters.append(WorkOrder.severity == severity_filter)
    if asset_id:
        filters.append(WorkOrder.asset_id == asset_id)
    role = user.role.name
    approval_scope = and_(
        WorkOrder.status == "AWAITING_APPROVAL",
        WorkOrder.external_parts_decision == "PENDING",
        WorkOrder.external_parts_requested_by != user.id,
    )
    if role not in get_settings().maintenance_approval_role_names:
        approval_scope = None
    if role == "MAINTENANCE_TECH":
        technician_scope = WorkOrder.assigned_to == user.id
        filters.append(
            or_(technician_scope, approval_scope)
            if approval_scope is not None
            else technician_scope
        )
    elif role == "LAB_MANAGER":
        manager_scope = WorkOrder.asset_id.in_(
            select(Asset.id)
            .join(Laboratory, Asset.laboratory_id == Laboratory.id)
            .where(Laboratory.manager_id == user.id)
        )
        filters.append(
            or_(manager_scope, approval_scope)
            if approval_scope is not None
            else manager_scope
        )
    elif role == "LAB_TECH":
        lab_tech_scope = WorkOrder.asset_id.in_(
            select(Asset.id)
            .join(Laboratory, Asset.laboratory_id == Laboratory.id)
            .where(Laboratory.department_id == user.department_id)
        )
        filters.append(
            or_(lab_tech_scope, approval_scope)
            if approval_scope is not None
            else lab_tech_scope
        )
    total = await session.scalar(
        select(func.count(WorkOrder.id)).where(*filters)
    ) or 0
    severity_order = case(
        (WorkOrder.severity == "CRITICAL", 0),
        (WorkOrder.severity == "HIGH", 1),
        (WorkOrder.severity == "MEDIUM", 2),
        else_=3,
    )
    records = list(
        (
            await session.scalars(
                _work_order_query()
                .where(*filters)
                .order_by(severity_order, WorkOrder.created_at, WorkOrder.id)
                .offset((page - 1) * size)
                .limit(size)
            )
        ).all()
    )
    for order in records:
        _ensure_read_access(user, order)
    histories = await _status_history(session, [order.id for order in records])
    return MaintenancePage(
        items=[_order_read(order, histories[order.id], user) for order in records],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


async def get_work_order(
    session: AsyncSession, order_id: uuid.UUID, user: User
) -> WorkOrderRead:
    return await _read_order(session, order_id, user)


async def create_work_order(
    session: AsyncSession,
    payload: FaultReportCreate,
    user: User,
    ip_address: str | None,
) -> WorkOrderRead:
    asset = await session.scalar(
        select(Asset)
        .options(joinedload(Asset.laboratory))
        .where(Asset.id == payload.asset_id)
        .with_for_update(of=Asset)
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    _ensure_report_access(user, asset)
    if asset.operational_status != "OPERATIONAL":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot open a work order for an asset in {asset.operational_status} status",
        )
    active_order = await session.scalar(
        select(WorkOrder.id)
        .where(
            WorkOrder.asset_id == asset.id,
            WorkOrder.status != "CLOSED",
        )
        .limit(1)
    )
    if active_order is not None:
        raise HTTPException(
            status_code=409,
            detail="This asset already has an open work order",
        )

    now = datetime.now(timezone.utc)
    year = now.year
    await session.execute(
        select(func.pg_advisory_xact_lock(func.hashtext(f"work-order:{year}")))
    )
    last_sequence = await session.scalar(
        select(func.split_part(WorkOrder.ticket_number, "-", 3).cast(Integer))
        .where(WorkOrder.ticket_number.like(f"WO-{year}-%"))
        .order_by(desc(func.split_part(WorkOrder.ticket_number, "-", 3).cast(Integer)))
        .limit(1)
    )
    # Ticket numbering is serialized by the transaction-level advisory lock.
    sequence = int(last_sequence or 0) + 1
    asset_old_values = _asset_values(asset)
    asset.operational_status = (
        "DEFECTIVE" if payload.severity == "CRITICAL" else "UNDER_MAINTENANCE"
    )
    asset.updated_at = now
    order = WorkOrder(
        ticket_number=f"WO-{year}-{sequence:04d}",
        asset_id=asset.id,
        reported_by=user.id,
        severity=payload.severity,
        failure_category=payload.failure_category,
        status="OPEN",
        fault_description=payload.fault_description,
    )
    session.add(order)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Work order could not be created") from None
    session.add_all(
        [
            _audit(
                user=user,
                action="WORK_ORDER_CREATED",
                entity_type="work_orders",
                entity_id=order.id,
                old_values=None,
                new_values=_work_order_values(order),
                ip_address=ip_address,
            ),
            _audit(
                user=user,
                action="ASSET_MAINTENANCE_REQUESTED",
                entity_type="assets",
                entity_id=asset.id,
                old_values=asset_old_values,
                new_values=_asset_values(asset),
                ip_address=ip_address,
            ),
        ]
    )
    await _commit(session, "Work order could not be created")
    logger.info(
        "maintenance.work_order_created",
        extra={"work_order_id": str(order.id), "ticket_number": order.ticket_number},
    )
    return await _read_order(session, order.id, user)


async def assign_work_order(
    session: AsyncSession,
    order_id: uuid.UUID,
    technician_id: uuid.UUID,
    user: User,
    ip_address: str | None,
) -> WorkOrderRead:
    order = await _get_order_record(session, order_id, lock=True)
    if order.status != "OPEN":
        raise HTTPException(
            status_code=409, detail="Only an OPEN work order can be assigned"
        )
    technician = await session.scalar(
        select(User)
        .options(joinedload(User.role))
        .where(User.id == technician_id)
    )
    if technician is None or not technician.is_active or technician.role.name != "MAINTENANCE_TECH":
        raise HTTPException(
            status_code=422,
            detail="Assignment must target an active MAINTENANCE_TECH account",
        )
    old_values = _work_order_values(order)
    order.assigned_to = technician.id
    order.status = "ASSIGNED"
    session.add(
        _audit(
            user=user,
            action="WORK_ORDER_ASSIGNED",
            entity_type="work_orders",
            entity_id=order.id,
            old_values=old_values,
            new_values=_work_order_values(order),
            ip_address=ip_address,
        )
    )
    await _commit(session, "Technician assignment could not be saved")
    logger.info("maintenance.work_order_assigned", extra={"work_order_id": str(order.id)})
    return await _read_order(session, order.id, user)


async def update_work_order_status(
    session: AsyncSession,
    order_id: uuid.UUID,
    status_update: WorkOrderStatusUpdate,
    user: User,
    ip_address: str | None,
) -> WorkOrderRead:
    order = await _get_order_record(session, order_id, lock=True)
    if order.assigned_to != user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the assigned Maintenance Technician can change this work order status",
        )
    allowed = {
        ("ASSIGNED", "IN_PROGRESS"),
        ("IN_PROGRESS", "AWAITING_PARTS"),
        ("AWAITING_PARTS", "IN_PROGRESS"),
    }
    if (order.status, status_update.status) not in allowed:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot transition a work order from {order.status} to {status_update.status}",
        )
    old_values = _work_order_values(order)
    order.status = status_update.status
    action = (
        "WORK_ORDER_STARTED"
        if status_update.status == "IN_PROGRESS" and old_values["status"] == "ASSIGNED"
        else "WORK_ORDER_STATUS_CHANGED"
    )
    session.add(
        _audit(
            user=user,
            action=action,
            entity_type="work_orders",
            entity_id=order.id,
            old_values=old_values,
            new_values=_work_order_values(order),
            ip_address=ip_address,
        )
    )
    await _commit(session, "Work order status could not be changed")
    return await _read_order(session, order.id, user)


async def request_external_parts_approval(
    session: AsyncSession,
    order_id: uuid.UUID,
    payload: ExternalPartsApprovalRequest,
    user: User,
    ip_address: str | None,
) -> WorkOrderRead:
    order = await _get_order_record(session, order_id, lock=True)
    if user.role.name != "MAINTENANCE_TECH" or order.assigned_to != user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the assigned Maintenance Technician can request external-parts approval",
        )
    if not get_settings().maintenance_approval_role_names:
        raise HTTPException(
            status_code=503,
            detail=(
                "External-parts approval requests are disabled until stakeholders "
                "designate authorized existing application roles"
            ),
        )
    if order.status not in {"IN_PROGRESS", "AWAITING_PARTS"}:
        raise HTTPException(
            status_code=409,
            detail="External-parts approval can be requested only for active repair work",
        )

    old_values = _work_order_values(order)
    order.external_parts_request_details = payload.request_details
    order.external_parts_requested_by = user.id
    order.external_parts_requested_at = datetime.now(timezone.utc)
    order.external_parts_previous_status = order.status
    order.external_parts_decision = "PENDING"
    order.external_parts_decided_by = None
    order.external_parts_decided_at = None
    order.external_parts_decision_notes = None
    order.status = "AWAITING_APPROVAL"
    session.add(
        _audit(
            user=user,
            action="EXTERNAL_PARTS_APPROVAL_REQUESTED",
            entity_type="work_orders",
            entity_id=order.id,
            old_values=old_values,
            new_values=_work_order_values(order),
            ip_address=ip_address,
        )
    )
    await _commit(session, "External-parts approval request could not be saved")
    logger.info(
        "maintenance.external_parts_approval_requested",
        extra={"work_order_id": str(order.id)},
    )
    return await _read_order(session, order.id, user)


async def decide_external_parts_approval(
    session: AsyncSession,
    order_id: uuid.UUID,
    payload: ExternalPartsApprovalDecisionUpdate,
    user: User,
    ip_address: str | None,
) -> WorkOrderRead:
    order = await _get_order_record(session, order_id, lock=True)
    settings = get_settings()
    approval_roles = settings.maintenance_approval_role_names
    if not approval_roles:
        raise HTTPException(
            status_code=503,
            detail=(
                "External-parts approval is disabled until stakeholders designate "
                "authorized existing application roles"
            ),
        )
    if user.role.name not in approval_roles:
        raise HTTPException(
            status_code=403,
            detail="Your role is not configured to decide external-parts approvals",
        )
    if order.external_parts_requested_by == user.id:
        raise HTTPException(
            status_code=403,
            detail="The user who requested external-parts approval cannot decide it",
        )
    if (
        order.status != "AWAITING_APPROVAL"
        or order.external_parts_decision != "PENDING"
        or order.external_parts_previous_status is None
    ):
        raise HTTPException(
            status_code=409,
            detail="This work order has no pending external-parts approval",
        )

    old_values = _work_order_values(order)
    order.external_parts_decision = payload.decision
    order.external_parts_decided_by = user.id
    order.external_parts_decided_at = datetime.now(timezone.utc)
    order.external_parts_decision_notes = payload.decision_notes
    if payload.decision == "APPROVED":
        order.status = order.external_parts_previous_status
        action: AuditAction = "EXTERNAL_PARTS_APPROVAL_APPROVED"
    else:
        # Rejection disposition is unresolved; keep the work order blocked.
        action = "EXTERNAL_PARTS_APPROVAL_REJECTED"
    session.add(
        _audit(
            user=user,
            action=action,
            entity_type="work_orders",
            entity_id=order.id,
            old_values=old_values,
            new_values=_work_order_values(order),
            ip_address=ip_address,
        )
    )
    await _commit(session, "External-parts approval decision could not be saved")
    logger.info(
        "maintenance.external_parts_approval_decided",
        extra={
            "work_order_id": str(order.id),
            "decision": payload.decision,
        },
    )
    return await _read_order(session, order.id, user)


async def add_maintenance_log(
    session: AsyncSession,
    order_id: uuid.UUID,
    payload: MaintenanceLogCreate,
    user: User,
    ip_address: str | None,
) -> WorkOrderRead:
    order = await _get_order_record(session, order_id, lock=True)
    if (
        user.role.name == "MAINTENANCE_TECH"
        and order.assigned_to != user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="Only the assigned Maintenance Technician can record repair activities",
        )
    if user.role.name not in {"MAINTENANCE_TECH", "ULMD_ADMIN"}:
        raise HTTPException(
            status_code=403,
            detail="You cannot record maintenance activities",
        )
    if order.status != "IN_PROGRESS":
        raise HTTPException(
            status_code=409,
            detail="Repair activities can be recorded only while the work order is IN_PROGRESS",
        )
    if order.assigned_to is None:
        raise HTTPException(
            status_code=409,
            detail="An assigned Maintenance Technician is required to record work",
        )
    old_values = _work_order_values(order)
    log = MaintenanceLog(
        work_order_id=order.id,
        technician_id=order.assigned_to,
        actions_taken=payload.actions_taken,
        spare_parts_used=payload.spare_parts_used or None,
        labor_hours=payload.labor_hours,
        outcome_condition=payload.outcome_condition,
    )
    session.add(log)
    order.status = "RESOLVED"
    order.resolved_at = datetime.now(timezone.utc)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Maintenance activity could not be saved") from None
    session.add_all(
        [
            _audit(
                user=user,
                action="MAINTENANCE_LOG_ADDED",
                entity_type="maintenance_logs",
                entity_id=log.id,
                old_values=None,
                new_values={
                    "work_order_id": str(log.work_order_id),
                    "technician_id": str(log.technician_id),
                    "actions_taken": log.actions_taken,
                    "spare_parts_used": log.spare_parts_used,
                    "labor_hours": str(log.labor_hours),
                    "outcome_condition": log.outcome_condition,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                },
                ip_address=ip_address,
            ),
            _audit(
                user=user,
                action="MAINTENANCE_LOG_ADDED",
                entity_type="work_orders",
                entity_id=order.id,
                old_values=old_values,
                new_values=_work_order_values(order),
                ip_address=ip_address,
            ),
        ]
    )
    await _commit(session, "Maintenance activity could not be saved")
    return await _read_order(session, order.id, user)


async def verify_work_order(
    session: AsyncSession,
    order_id: uuid.UUID,
    payload: MaintenanceVerification,
    user: User,
    ip_address: str | None,
) -> WorkOrderRead:
    order = await session.scalar(
        select(WorkOrder)
        .options(joinedload(WorkOrder.asset).joinedload(Asset.laboratory))
        .where(WorkOrder.id == order_id)
        .with_for_update(of=WorkOrder)
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Work order not found")
    if user.role.name == "LAB_MANAGER":
        if (
            order.asset.laboratory.manager_id != user.id
            or order.asset.laboratory.department_id != user.department_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Only the designated custodian Lab Manager can verify this repair",
            )
    elif user.role.name != "ULMD_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only the custodian Lab Manager or ULMD_ADMIN can verify a repair",
        )
    if order.status != "RESOLVED":
        raise HTTPException(
            status_code=409, detail="Only a RESOLVED work order can be verified"
        )

    last_log = await session.scalar(
        select(MaintenanceLog)
        .where(MaintenanceLog.work_order_id == order.id)
        .order_by(desc(MaintenanceLog.created_at), desc(MaintenanceLog.id))
        .limit(1)
    )
    if last_log is None:
        raise HTTPException(
            status_code=409, detail="A maintenance activity is required before verification"
        )
    if payload.confirmed and last_log.outcome_condition != "OPERATIONAL":
        raise HTTPException(
            status_code=409,
            detail=(
                "Only an OPERATIONAL repair outcome can close a work order. "
                "The approved closure policy for degraded or unrepairable assets is unresolved."
            ),
        )

    old_values = _work_order_values(order)
    asset = await session.scalar(
        select(Asset).where(Asset.id == order.asset_id).with_for_update()
    )
    if asset is None:
        raise HTTPException(status_code=409, detail="Work order asset no longer exists")
    asset_old_values = _asset_values(asset)
    order.verified_by = user.id
    order.verification_notes = payload.verification_notes
    if payload.confirmed:
        order.status = "CLOSED"
        order.closed_at = datetime.now(timezone.utc)
        asset.operational_status = "OPERATIONAL"
        asset.updated_at = datetime.now(timezone.utc)
    else:
        order.status = "IN_PROGRESS"
        order.resolved_at = None
        order.closed_at = None
    action = "WORK_ORDER_CLOSED" if payload.confirmed else "WORK_ORDER_REPAIR_REJECTED"
    audit_rows = [
        _audit(
            user=user,
            action=action,
            entity_type="work_orders",
            entity_id=order.id,
            old_values=old_values,
            new_values=_work_order_values(order),
            ip_address=ip_address,
        )
    ]
    if payload.confirmed:
        audit_rows.append(
            _audit(
                user=user,
                action="ASSET_MAINTENANCE_CLOSED",
                entity_type="assets",
                entity_id=asset.id,
                old_values=asset_old_values,
                new_values=_asset_values(asset),
                ip_address=ip_address,
            )
        )
    session.add_all(audit_rows)
    await _commit(session, "Work order verification could not be saved")
    logger.info(
        "maintenance.work_order_verified",
        extra={"work_order_id": str(order.id), "closed": payload.confirmed},
    )
    return await _read_order(session, order.id, user)
