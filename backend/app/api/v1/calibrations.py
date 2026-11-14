import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.calibration import (
    CalibrationCreate,
    CalibrationDueRead,
    CalibrationPage,
    CalibrationRead,
)
from app.services import calibration_service

router = APIRouter(prefix="/calibrations", tags=["calibrations"])
Page = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=CalibrationPage[CalibrationRead])
async def read_calibrations(
    page: Page = 1,
    size: PageSize = 20,
    asset_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(
        require_roles("ULMD_ADMIN", "MAINTENANCE_TECH", "AUDITOR")
    ),
):
    return await calibration_service.list_calibrations(
        session, page=page, size=size, asset_id=asset_id
    )


@router.get("/due", response_model=CalibrationPage[CalibrationDueRead])
async def read_due_calibrations(
    within_days: Annotated[int, Query(ge=0)],
    page: Page = 1,
    size: PageSize = 20,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
):
    return await calibration_service.list_due_calibrations(
        session, within_days=within_days, page=page, size=size
    )


@router.post(
    "",
    response_model=CalibrationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_calibration(
    payload: CalibrationCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("ULMD_ADMIN", "MAINTENANCE_TECH")),
):
    return await calibration_service.create_calibration(
        session, payload, user, _client_ip(request)
    )
