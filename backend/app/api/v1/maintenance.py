import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.maintenance import (
    ExternalPartsApprovalDecisionUpdate,
    ExternalPartsApprovalRequest,
    FaultReportCreate,
    MaintenanceLogCreate,
    MaintenancePage,
    MaintenanceVerification,
    TechnicianAssignment,
    WorkOrderRead,
    WorkOrderSeverity,
    WorkOrderStatus,
    WorkOrderStatusUpdate,
)
from app.services import maintenance_service

router = APIRouter(prefix="/work-orders", tags=["maintenance"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=MaintenancePage[WorkOrderRead])
async def read_work_orders(
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: WorkOrderStatus | None = Query(default=None, alias="status"),
    severity: WorkOrderSeverity | None = None,
    asset_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(
        require_roles(
            "ULMD_ADMIN",
            "MAINTENANCE_TECH",
            "LAB_MANAGER",
            "LAB_TECH",
            "AUDITOR",
        )
    ),
):
    return await maintenance_service.list_work_orders(
        session,
        page=page,
        size=size,
        status_filter=status_filter,
        severity_filter=severity,
        asset_id=asset_id,
        user=user,
    )


@router.post(
    "",
    response_model=WorkOrderRead,
    status_code=status.HTTP_201_CREATED,
)
async def report_fault(
    payload: FaultReportCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("ULMD_ADMIN", "LAB_MANAGER", "LAB_TECH")),
):
    return await maintenance_service.create_work_order(
        session, payload, user, _client_ip(request)
    )


@router.get("/{order_id}", response_model=WorkOrderRead)
async def read_work_order(
    order_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(
        require_roles(
            "ULMD_ADMIN",
            "MAINTENANCE_TECH",
            "LAB_MANAGER",
            "LAB_TECH",
            "AUDITOR",
        )
    ),
):
    return await maintenance_service.get_work_order(session, order_id, user)


@router.put("/{order_id}/assign", response_model=WorkOrderRead)
async def assign_work_order(
    order_id: uuid.UUID,
    payload: TechnicianAssignment,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("ULMD_ADMIN")),
):
    return await maintenance_service.assign_work_order(
        session, order_id, payload.assigned_to, user, _client_ip(request)
    )


@router.put("/{order_id}/status", response_model=WorkOrderRead)
async def change_work_order_status(
    order_id: uuid.UUID,
    payload: WorkOrderStatusUpdate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("MAINTENANCE_TECH")),
):
    return await maintenance_service.update_work_order_status(
        session, order_id, payload, user, _client_ip(request)
    )


@router.post(
    "/{order_id}/external-parts-approval",
    response_model=WorkOrderRead,
)
async def request_external_parts_approval(
    order_id: uuid.UUID,
    payload: ExternalPartsApprovalRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    return await maintenance_service.request_external_parts_approval(
        session, order_id, payload, user, _client_ip(request)
    )


@router.put(
    "/{order_id}/external-parts-approval/decision",
    response_model=WorkOrderRead,
)
async def decide_external_parts_approval(
    order_id: uuid.UUID,
    payload: ExternalPartsApprovalDecisionUpdate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    return await maintenance_service.decide_external_parts_approval(
        session, order_id, payload, user, _client_ip(request)
    )


@router.post(
    "/{order_id}/logs",
    response_model=WorkOrderRead,
    status_code=status.HTTP_201_CREATED,
)
async def record_maintenance_activity(
    order_id: uuid.UUID,
    payload: MaintenanceLogCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("MAINTENANCE_TECH", "ULMD_ADMIN")),
):
    return await maintenance_service.add_maintenance_log(
        session, order_id, payload, user, _client_ip(request)
    )


@router.put("/{order_id}/close", response_model=WorkOrderRead)
async def verify_or_reject_repair(
    order_id: uuid.UUID,
    payload: MaintenanceVerification,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("LAB_MANAGER", "ULMD_ADMIN")),
):
    return await maintenance_service.verify_work_order(
        session, order_id, payload, user, _client_ip(request)
    )
