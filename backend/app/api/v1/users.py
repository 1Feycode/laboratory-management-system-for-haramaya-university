from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.user import (
    DepartmentOption,
    RoleName,
    UserCreate,
    UserPage,
    UserRead,
    UserUpdate,
)
from app.services.user_service import (
    create_user,
    get_user,
    list_departments,
    list_users,
    update_user,
)

router = APIRouter(
    prefix="/users",
    tags=["user management"],
)


@router.get("/departments", response_model=list[DepartmentOption])
async def read_departments(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles("ULMD_ADMIN")),
) -> list[DepartmentOption]:
    return await list_departments(session)


@router.get("", response_model=UserPage)
async def read_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    role: RoleName | None = None,
    department_id: UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles("ULMD_ADMIN")),
) -> UserPage:
    return await list_users(
        session,
        page=page,
        size=size,
        role=role,
        department_id=department_id,
    )


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def provision_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles("ULMD_ADMIN")),
) -> UserRead:
    return await create_user(session, payload)


@router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles("ULMD_ADMIN")),
) -> UserRead:
    return await get_user(session, user_id)


@router.patch("/{user_id}", response_model=UserRead)
async def modify_user(
    user_id: UUID,
    payload: UserUpdate,
    session: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_roles("ULMD_ADMIN")),
) -> UserRead:
    return await update_user(session, user_id, payload, actor_id=admin.id)
