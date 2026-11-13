import asyncio
import logging
import math
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.models.organization import Department
from app.models.user import Role, User
from app.schemas.user import (
    DepartmentOption,
    RoleName,
    UserCreate,
    UserPage,
    UserRead,
    UserUpdate,
)

logger = logging.getLogger(__name__)
SCOPED_ROLES = {"LAB_MANAGER", "LAB_TECH"}


def _read_user(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.name,
        department_id=user.department_id,
        is_active=user.is_active,
        created_at=user.created_at,
    )


async def list_users(
    session: AsyncSession,
    *,
    page: int,
    size: int,
    role: RoleName | None,
    department_id: uuid.UUID | None,
) -> UserPage:
    filters = []
    if role is not None:
        filters.append(User.role_id == select(Role.id).where(Role.name == role).scalar_subquery())
    if department_id is not None:
        filters.append(User.department_id == department_id)

    total = await session.scalar(select(func.count(User.id)).where(*filters)) or 0
    result = await session.scalars(
        select(User)
        .options(selectinload(User.role))
        .where(*filters)
        .order_by(User.created_at.desc(), User.id)
        .offset((page - 1) * size)
        .limit(size)
    )
    return UserPage(
        items=[_read_user(user) for user in result],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


async def get_user(session: AsyncSession, user_id: uuid.UUID) -> UserRead:
    user = await session.scalar(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _read_user(user)


async def list_departments(session: AsyncSession) -> list[DepartmentOption]:
    result = await session.scalars(
        select(Department).order_by(Department.name, Department.code)
    )
    return [
        DepartmentOption(id=department.id, name=department.name, code=department.code)
        for department in result
    ]


async def create_user(session: AsyncSession, payload: UserCreate) -> UserRead:
    role = await session.scalar(select(Role).where(Role.name == payload.role))
    if role is None:
        raise HTTPException(status_code=500, detail="Configured user role is unavailable")
    await _ensure_department(session, payload.department_id, payload.role)

    user = User(
        email=str(payload.email).casefold(),
        hashed_password=await asyncio.to_thread(
            hash_password, payload.password.get_secret_value()
        ),
        full_name=payload.full_name,
        role=role,
        department_id=payload.department_id,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        logger.info("users.create_conflict", extra={"role": payload.role})
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        ) from None
    await session.refresh(user, attribute_names=["role"])
    logger.info(
        "users.created",
        extra={"user_id": str(user.id), "role": payload.role},
    )
    return _read_user(user)


async def update_user(
    session: AsyncSession,
    user_id: uuid.UUID,
    payload: UserUpdate,
    actor_id: uuid.UUID,
) -> UserRead:
    user = await session.scalar(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    changes = payload.model_dump(exclude_unset=True)
    role_name = changes.get("role", user.role.name)
    department_id = changes.get("department_id", user.department_id)
    await _ensure_department(session, department_id, role_name)

    changing_admin_status = (
        user.is_active
        and user.role.name == "ULMD_ADMIN"
        and (
            changes.get("is_active") is False
            or role_name != "ULMD_ADMIN"
        )
    )
    if changing_admin_status:
        active_admins = await session.scalar(
            select(func.count(User.id))
            .join(Role, User.role_id == Role.id)
            .where(
                Role.name == "ULMD_ADMIN",
                User.is_active.is_(True),
                User.id != user.id,
            )
        )
        if not active_admins:
            raise HTTPException(
                status_code=409,
                detail="The last active ULMD_ADMIN account cannot be deactivated or demoted",
            )

    old_role = user.role.name
    was_active = user.is_active
    if "email" in changes:
        user.email = str(changes["email"]).casefold()
    if "full_name" in changes:
        user.full_name = changes["full_name"]
    if "is_active" in changes:
        user.is_active = changes["is_active"]
    if "department_id" in changes:
        user.department_id = changes["department_id"]
    if "role" in changes:
        role = await session.scalar(select(Role).where(Role.name == changes["role"]))
        if role is None:
            raise HTTPException(status_code=500, detail="Configured user role is unavailable")
        user.role = role

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The requested user update conflicts with existing data",
        ) from None
    await session.refresh(user, attribute_names=["role"])
    logger.info(
        "users.updated",
        extra={
            "user_id": str(user.id),
            "role": user.role.name,
            "is_active": user.is_active,
        },
    )
    if old_role != user.role.name:
        logger.info(
            "auth.role_changed",
            extra={
                "actor_id": str(actor_id),
                "target_user_id": str(user.id),
                "old_role": old_role,
                "new_role": user.role.name,
            },
        )
    if was_active and not user.is_active:
        logger.info(
            "auth.user_deactivated",
            extra={"actor_id": str(actor_id), "target_user_id": str(user.id)},
        )
    return _read_user(user)


async def _ensure_department(
    session: AsyncSession,
    department_id: uuid.UUID | None,
    role: str,
) -> None:
    if role in SCOPED_ROLES and department_id is None:
        raise HTTPException(
            status_code=422,
            detail=f"{role} accounts require a department assignment",
        )
    if department_id is not None:
        department = await session.get(Department, department_id)
        if department is None:
            raise HTTPException(status_code=422, detail="Department does not exist")
