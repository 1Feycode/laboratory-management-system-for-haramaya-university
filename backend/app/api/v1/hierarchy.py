import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.organization import (
    CollegeCreate,
    CollegeRead,
    CollegeUpdate,
    DepartmentCreate,
    DepartmentRead,
    DepartmentUpdate,
    LabType,
    LaboratoryCreate,
    LaboratoryRead,
    LaboratoryUpdate,
    OrganizationPage,
    RoomCreate,
    RoomRead,
    RoomUpdate,
)
from app.services import organization_service as service

router = APIRouter(prefix="/hierarchy", tags=["organizational hierarchy"])
Page = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]
Search = Annotated[str | None, Query(max_length=100)]


@router.get("/colleges", response_model=OrganizationPage[CollegeRead])
async def read_colleges(
    page: Page = 1,
    size: PageSize = 20,
    search: Search = None,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
):
    return await service.list_colleges(session, page=page, size=size, search=search)


@router.post(
    "/colleges",
    response_model=CollegeRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_college(
    payload: CollegeCreate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles("ULMD_ADMIN")),
):
    return await service.create_college(session, payload)


@router.get("/colleges/{college_id}", response_model=CollegeRead)
async def read_college(
    college_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
):
    return await service.get_college(session, college_id)


@router.patch("/colleges/{college_id}", response_model=CollegeRead)
async def update_college(
    college_id: uuid.UUID,
    payload: CollegeUpdate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles("ULMD_ADMIN")),
):
    return await service.update_college(session, college_id, payload)


@router.delete("/colleges/{college_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_college(
    college_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles("ULMD_ADMIN")),
):
    await service.delete_college(session, college_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/departments", response_model=OrganizationPage[DepartmentRead])
async def read_departments(
    page: Page = 1,
    size: PageSize = 20,
    search: Search = None,
    college_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
):
    return await service.list_departments(
        session,
        page=page,
        size=size,
        search=search,
        college_id=college_id,
    )


@router.post(
    "/departments",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_department(
    payload: DepartmentCreate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles("ULMD_ADMIN")),
):
    return await service.create_department(session, payload)


@router.get("/departments/{department_id}", response_model=DepartmentRead)
async def read_department(
    department_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
):
    return await service.get_department(session, department_id)


@router.patch("/departments/{department_id}", response_model=DepartmentRead)
async def update_department(
    department_id: uuid.UUID,
    payload: DepartmentUpdate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles("ULMD_ADMIN")),
):
    return await service.update_department(session, department_id, payload)


@router.delete("/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles("ULMD_ADMIN")),
):
    await service.delete_department(session, department_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/laboratories", response_model=OrganizationPage[LaboratoryRead])
async def read_laboratories(
    page: Page = 1,
    size: PageSize = 20,
    search: Search = None,
    department_id: uuid.UUID | None = None,
    lab_type: LabType | None = None,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
):
    return await service.list_laboratories(
        session,
        page=page,
        size=size,
        search=search,
        department_id=department_id,
        lab_type=lab_type,
    )


@router.post(
    "/laboratories",
    response_model=LaboratoryRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_laboratory(
    payload: LaboratoryCreate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles("ULMD_ADMIN")),
):
    return await service.create_laboratory(session, payload)


@router.get("/laboratories/{laboratory_id}", response_model=LaboratoryRead)
async def read_laboratory(
    laboratory_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
):
    return await service.get_laboratory(session, laboratory_id)


@router.patch("/laboratories/{laboratory_id}", response_model=LaboratoryRead)
async def update_laboratory(
    laboratory_id: uuid.UUID,
    payload: LaboratoryUpdate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles("ULMD_ADMIN")),
):
    return await service.update_laboratory(session, laboratory_id, payload)


@router.delete("/laboratories/{laboratory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_laboratory(
    laboratory_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles("ULMD_ADMIN")),
):
    await service.delete_laboratory(session, laboratory_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/rooms", response_model=OrganizationPage[RoomRead])
async def read_rooms(
    page: Page = 1,
    size: PageSize = 20,
    search: Search = None,
    laboratory_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
):
    return await service.list_rooms(
        session,
        page=page,
        size=size,
        search=search,
        laboratory_id=laboratory_id,
    )


@router.post(
    "/rooms",
    response_model=RoomRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_room(
    payload: RoomCreate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles("ULMD_ADMIN")),
):
    return await service.create_room(session, payload)


@router.get("/rooms/{room_id}", response_model=RoomRead)
async def read_room(
    room_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
):
    return await service.get_room(session, room_id)


@router.patch("/rooms/{room_id}", response_model=RoomRead)
async def update_room(
    room_id: uuid.UUID,
    payload: RoomUpdate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles("ULMD_ADMIN")),
):
    return await service.update_room(session, room_id, payload)


@router.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles("ULMD_ADMIN")),
):
    await service.delete_room(session, room_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
