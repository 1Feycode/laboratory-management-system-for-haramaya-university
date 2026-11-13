import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.transfer import (
    TransferAcceptance,
    TransferCreate,
    TransferPage,
    TransferRead,
    TransferRejection,
    TransferStatus,
)
from app.services import transfer_service

router = APIRouter(prefix="/transfers", tags=["asset transfers"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=TransferPage)
async def read_transfers(
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: TransferStatus | None = Query(default=None, alias="status"),
    asset_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(
        require_roles("ULMD_ADMIN", "LAB_MANAGER", "AUDITOR")
    ),
):
    return await transfer_service.list_transfers(
        session,
        page=page,
        size=size,
        status_filter=status_filter,
        asset_id=asset_id,
        user=user,
    )


@router.post(
    "",
    response_model=TransferRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_transfer(
    payload: TransferCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("ULMD_ADMIN", "LAB_MANAGER")),
):
    return await transfer_service.create_transfer(
        session, payload, user, _client_ip(request)
    )


@router.get("/{transfer_id}", response_model=TransferRead)
async def read_transfer(
    transfer_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(
        require_roles("ULMD_ADMIN", "LAB_MANAGER", "AUDITOR")
    ),
):
    return await transfer_service.get_transfer(session, transfer_id, user)


@router.put("/{transfer_id}/accept", response_model=TransferRead)
async def accept_transfer(
    transfer_id: uuid.UUID,
    payload: TransferAcceptance,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("ULMD_ADMIN", "LAB_MANAGER")),
):
    return await transfer_service.accept_transfer(
        session, transfer_id, payload, user, _client_ip(request)
    )


@router.put("/{transfer_id}/reject", response_model=TransferRead)
async def reject_transfer(
    transfer_id: uuid.UUID,
    payload: TransferRejection,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("ULMD_ADMIN", "LAB_MANAGER")),
):
    return await transfer_service.reject_transfer(
        session, transfer_id, payload, user, _client_ip(request)
    )


@router.put("/{transfer_id}/approve", response_model=TransferRead)
async def approve_transfer(
    transfer_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("ULMD_ADMIN")),
):
    return await transfer_service.approve_transfer(
        session, transfer_id, user, _client_ip(request)
    )
