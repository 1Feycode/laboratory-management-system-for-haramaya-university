from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.reports import (
    CalibrationComplianceReport,
    DashboardReport,
    DowntimeReport,
)
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])
NonNegativeDays = Annotated[int, Query(ge=0)]


@router.get("/dashboard", response_model=DashboardReport)
async def read_dashboard(
    within_days: NonNegativeDays,
    college_id: UUID | None = None,
    department_id: UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(
        require_roles("ULMD_ADMIN", "LAB_MANAGER", "AUDITOR")
    ),
):
    return await report_service.get_dashboard(
        session,
        user,
        college_id=college_id,
        department_id=department_id,
        date_from=date_from,
        date_to=date_to,
        within_days=within_days,
    )


@router.get("/downtime", response_model=DowntimeReport)
async def read_downtime_report(
    date_from: date,
    date_to: date,
    college_id: UUID | None = None,
    department_id: UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(
        require_roles("ULMD_ADMIN", "LAB_MANAGER", "AUDITOR")
    ),
):
    return await report_service.get_downtime_report(
        session,
        user,
        college_id=college_id,
        department_id=department_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get(
    "/calibration-compliance",
    response_model=CalibrationComplianceReport,
)
async def read_calibration_compliance(
    within_days: NonNegativeDays,
    college_id: UUID | None = None,
    department_id: UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(
        require_roles("ULMD_ADMIN", "LAB_MANAGER", "AUDITOR")
    ),
):
    return await report_service.get_calibration_compliance(
        session,
        user,
        college_id=college_id,
        department_id=department_id,
        date_from=date_from,
        date_to=date_to,
        within_days=within_days,
    )


@router.get("/inventory")
async def export_inventory(
    college_id: UUID | None = None,
    department_id: UUID | None = None,
    status: Literal[
        "OPERATIONAL",
        "UNDER_MAINTENANCE",
        "DEFECTIVE",
        "TRANSFER_PENDING",
        "DECOMMISSIONED",
    ]
    | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("ULMD_ADMIN", "AUDITOR")),
):
    content = await report_service.export_inventory_csv(
        session,
        user,
        college_id=college_id,
        department_id=department_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="hu-laboratory-inventory.csv"'
        },
    )
