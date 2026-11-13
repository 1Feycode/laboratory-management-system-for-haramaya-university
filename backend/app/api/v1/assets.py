import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.asset import (
    AssetCategoryCreate,
    AssetCategoryRead,
    AssetCategoryUpdate,
    AssetCreate,
    AssetPage,
    AssetRead,
    AssetStatus,
    AssetUpdate,
)
from app.services import asset_service

assets_router = APIRouter(prefix="/assets", tags=["assets"])
categories_router = APIRouter(prefix="/asset-categories", tags=["asset categories"])

Page = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]
Search = Annotated[str | None, Query(max_length=100)]
SortBy = Literal[
    "asset_code",
    "created_at",
    "model_number",
    "operational_status",
    "purchase_date",
]


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@categories_router.get("", response_model=AssetPage[AssetCategoryRead])
async def read_categories(
    page: Page = 1,
    size: PageSize = 100,
    search: Search = None,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
):
    return await asset_service.list_categories(
        session, page=page, size=size, search=search
    )


@categories_router.post(
    "",
    response_model=AssetCategoryRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    payload: AssetCategoryCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("ULMD_ADMIN")),
):
    return await asset_service.create_category(
        session, payload, user, _client_ip(request)
    )


@categories_router.get("/{category_id}", response_model=AssetCategoryRead)
async def read_category(
    category_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
):
    return await asset_service.get_category(session, category_id)


@categories_router.patch("/{category_id}", response_model=AssetCategoryRead)
async def update_category(
    category_id: uuid.UUID,
    payload: AssetCategoryUpdate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("ULMD_ADMIN")),
):
    return await asset_service.update_category(
        session, category_id, payload, user, _client_ip(request)
    )


@categories_router.delete(
    "/{category_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_category(
    category_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("ULMD_ADMIN")),
):
    await asset_service.delete_category(
        session, category_id, user, _client_ip(request)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@assets_router.get("", response_model=AssetPage[AssetRead])
async def read_assets(
    page: Page = 1,
    size: PageSize = 20,
    search: Search = None,
    college_id: uuid.UUID | None = None,
    department_id: uuid.UUID | None = None,
    laboratory_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    operational_status: AssetStatus | None = Query(default=None, alias="status"),
    sort_by: SortBy = "asset_code",
    sort_order: Literal["asc", "desc"] = "asc",
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
):
    return await asset_service.list_assets(
        session,
        page=page,
        size=size,
        search=search,
        college_id=college_id,
        department_id=department_id,
        laboratory_id=laboratory_id,
        category_id=category_id,
        operational_status=operational_status,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@assets_router.post(
    "",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_asset(
    payload: AssetCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("ULMD_ADMIN", "LAB_MANAGER")),
):
    return await asset_service.create_asset(
        session, payload, user, _client_ip(request)
    )


@assets_router.get("/lookup/{asset_code}", response_model=AssetRead)
async def lookup_asset(
    asset_code: str,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
):
    return await asset_service.get_asset_by_code(session, asset_code)


@assets_router.get("/{asset_id}/qr", response_class=Response)
async def read_asset_qr(
    asset_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
):
    return await asset_service.get_asset_qr(session, asset_id)


@assets_router.get("/{asset_id}", response_model=AssetRead)
async def read_asset(
    asset_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
):
    return await asset_service.get_asset(session, asset_id)


@assets_router.patch("/{asset_id}", response_model=AssetRead)
async def update_asset(
    asset_id: uuid.UUID,
    payload: AssetUpdate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles("ULMD_ADMIN", "LAB_MANAGER")),
):
    return await asset_service.update_asset(
        session, asset_id, payload, user, _client_ip(request)
    )
