import logging
import math
import uuid

from fastapi import HTTPException
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.organization import College, Department, Laboratory, Room
from app.models.user import User
from app.schemas.organization import (
    CollegeCreate,
    CollegeRead,
    CollegeUpdate,
    DepartmentCreate,
    DepartmentRead,
    DepartmentUpdate,
    LaboratoryCreate,
    LaboratoryRead,
    LaboratoryUpdate,
    OrganizationPage,
    RoomCreate,
    RoomRead,
    RoomUpdate,
)

logger = logging.getLogger(__name__)


async def _commit(session: AsyncSession, detail: str) -> None:
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail=detail) from None


async def _delete(
    session: AsyncSession,
    statement,
    *,
    missing_detail: str,
    conflict_detail: str,
) -> None:
    try:
        result = await session.execute(statement)
        if result.rowcount == 0:
            await session.rollback()
            raise HTTPException(status_code=404, detail=missing_detail)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail=conflict_detail) from None


async def _ensure_exists(
    session: AsyncSession, model: type, record_id: uuid.UUID, label: str
) -> None:
    if await session.get(model, record_id) is None:
        raise HTTPException(
            status_code=422,
            detail=f"{label} does not exist",
        )


def _college_read(college: College) -> CollegeRead:
    return CollegeRead.model_validate(college)


def _department_read(department: Department) -> DepartmentRead:
    return DepartmentRead(
        id=department.id,
        college_id=department.college_id,
        college_name=department.college.name,
        name=department.name,
        code=department.code,
        created_at=department.created_at,
    )


def _laboratory_read(laboratory: Laboratory) -> LaboratoryRead:
    return LaboratoryRead(
        id=laboratory.id,
        department_id=laboratory.department_id,
        department_name=laboratory.department.name,
        college_name=laboratory.department.college.name,
        name=laboratory.name,
        lab_type=laboratory.lab_type,
        manager_id=laboratory.manager_id,
        manager_name=laboratory.manager.full_name if laboratory.manager else None,
        created_at=laboratory.created_at,
    )


def _room_read(room: Room) -> RoomRead:
    return RoomRead(
        id=room.id,
        laboratory_id=room.laboratory_id,
        laboratory_name=room.laboratory.name,
        department_name=room.laboratory.department.name,
        college_name=room.laboratory.department.college.name,
        room_number=room.room_number,
        building_name=room.building_name,
        created_at=room.created_at,
    )


async def list_colleges(
    session: AsyncSession, *, page: int, size: int, search: str | None
) -> OrganizationPage[CollegeRead]:
    filters = []
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(or_(College.name.ilike(pattern), College.code.ilike(pattern)))
    total = await session.scalar(select(func.count(College.id)).where(*filters)) or 0
    records = await session.scalars(
        select(College)
        .where(*filters)
        .order_by(College.name, College.id)
        .offset((page - 1) * size)
        .limit(size)
    )
    return OrganizationPage(
        items=[_college_read(item) for item in records],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


async def get_college(session: AsyncSession, record_id: uuid.UUID) -> CollegeRead:
    record = await session.get(College, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="College not found")
    return _college_read(record)


async def create_college(
    session: AsyncSession, payload: CollegeCreate
) -> CollegeRead:
    record = College(name=payload.name, code=payload.code)
    session.add(record)
    await _commit(session, "College name or code already exists")
    await session.refresh(record)
    logger.info("hierarchy.college_created", extra={"college_id": str(record.id)})
    return _college_read(record)


async def update_college(
    session: AsyncSession, record_id: uuid.UUID, payload: CollegeUpdate
) -> CollegeRead:
    record = await session.get(College, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="College not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await _commit(session, "College name or code already exists")
    await session.refresh(record)
    logger.info("hierarchy.college_updated", extra={"college_id": str(record.id)})
    return _college_read(record)


async def delete_college(session: AsyncSession, record_id: uuid.UUID) -> None:
    await _delete(
        session,
        delete(College).where(College.id == record_id),
        missing_detail="College not found",
        conflict_detail="College is referenced by departments and cannot be deleted",
    )
    logger.info("hierarchy.college_deleted", extra={"college_id": str(record_id)})


async def list_departments(
    session: AsyncSession,
    *,
    page: int,
    size: int,
    search: str | None,
    college_id: uuid.UUID | None,
) -> OrganizationPage[DepartmentRead]:
    filters = []
    if college_id:
        filters.append(Department.college_id == college_id)
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(or_(Department.name.ilike(pattern), Department.code.ilike(pattern)))
    total = await session.scalar(
        select(func.count(Department.id)).where(*filters)
    ) or 0
    records = await session.scalars(
        select(Department)
        .options(joinedload(Department.college))
        .where(*filters)
        .order_by(Department.name, Department.code, Department.id)
        .offset((page - 1) * size)
        .limit(size)
    )
    return OrganizationPage(
        items=[_department_read(item) for item in records],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


async def get_department(
    session: AsyncSession, record_id: uuid.UUID
) -> DepartmentRead:
    record = await session.scalar(
        select(Department)
        .options(joinedload(Department.college))
        .where(Department.id == record_id)
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return _department_read(record)


async def create_department(
    session: AsyncSession, payload: DepartmentCreate
) -> DepartmentRead:
    await _ensure_exists(session, College, payload.college_id, "College")
    record = Department(
        college_id=payload.college_id,
        name=payload.name,
        code=payload.code,
    )
    session.add(record)
    await _commit(session, "Department code already exists in this college")
    return await get_department(session, record.id)


async def update_department(
    session: AsyncSession, record_id: uuid.UUID, payload: DepartmentUpdate
) -> DepartmentRead:
    record = await session.get(Department, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Department not found")
    changes = payload.model_dump(exclude_unset=True)
    if "college_id" in changes:
        await _ensure_exists(session, College, changes["college_id"], "College")
    for field, value in changes.items():
        setattr(record, field, value)
    await _commit(session, "Department code already exists in this college")
    return await get_department(session, record_id)


async def delete_department(session: AsyncSession, record_id: uuid.UUID) -> None:
    await _delete(
        session,
        delete(Department).where(Department.id == record_id),
        missing_detail="Department not found",
        conflict_detail="Department is referenced by laboratories and cannot be deleted",
    )
    logger.info("hierarchy.department_deleted", extra={"department_id": str(record_id)})


async def list_laboratories(
    session: AsyncSession,
    *,
    page: int,
    size: int,
    search: str | None,
    department_id: uuid.UUID | None,
    lab_type: str | None,
) -> OrganizationPage[LaboratoryRead]:
    filters = []
    if department_id:
        filters.append(Laboratory.department_id == department_id)
    if lab_type:
        filters.append(Laboratory.lab_type == lab_type)
    if search:
        filters.append(Laboratory.name.ilike(f"%{search.strip()}%"))
    total = await session.scalar(
        select(func.count(Laboratory.id)).where(*filters)
    ) or 0
    records = await session.scalars(
        select(Laboratory)
        .options(
            joinedload(Laboratory.department).joinedload(Department.college),
            joinedload(Laboratory.manager),
        )
        .where(*filters)
        .order_by(Laboratory.name, Laboratory.id)
        .offset((page - 1) * size)
        .limit(size)
    )
    return OrganizationPage(
        items=[_laboratory_read(item) for item in records],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


async def get_laboratory(
    session: AsyncSession, record_id: uuid.UUID
) -> LaboratoryRead:
    record = await session.scalar(
        select(Laboratory)
        .options(
            joinedload(Laboratory.department).joinedload(Department.college),
            joinedload(Laboratory.manager),
        )
        .where(Laboratory.id == record_id)
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Laboratory not found")
    return _laboratory_read(record)


async def create_laboratory(
    session: AsyncSession, payload: LaboratoryCreate
) -> LaboratoryRead:
    await _ensure_exists(session, Department, payload.department_id, "Department")
    if payload.manager_id:
        await _ensure_exists(session, User, payload.manager_id, "Manager")
    record = Laboratory(**payload.model_dump())
    session.add(record)
    await _commit(session, "Laboratory references invalid organizational data")
    return await get_laboratory(session, record.id)


async def update_laboratory(
    session: AsyncSession, record_id: uuid.UUID, payload: LaboratoryUpdate
) -> LaboratoryRead:
    record = await session.get(Laboratory, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Laboratory not found")
    changes = payload.model_dump(exclude_unset=True)
    if "department_id" in changes:
        await _ensure_exists(session, Department, changes["department_id"], "Department")
    if changes.get("manager_id"):
        await _ensure_exists(session, User, changes["manager_id"], "Manager")
    for field, value in changes.items():
        setattr(record, field, value)
    await _commit(session, "Laboratory references invalid organizational data")
    return await get_laboratory(session, record_id)


async def delete_laboratory(session: AsyncSession, record_id: uuid.UUID) -> None:
    await _delete(
        session,
        delete(Laboratory).where(Laboratory.id == record_id),
        missing_detail="Laboratory not found",
        conflict_detail="Laboratory is referenced by rooms or assets and cannot be deleted",
    )
    logger.info("hierarchy.laboratory_deleted", extra={"laboratory_id": str(record_id)})


async def list_rooms(
    session: AsyncSession,
    *,
    page: int,
    size: int,
    search: str | None,
    laboratory_id: uuid.UUID | None,
) -> OrganizationPage[RoomRead]:
    filters = []
    if laboratory_id:
        filters.append(Room.laboratory_id == laboratory_id)
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(Room.room_number.ilike(pattern), Room.building_name.ilike(pattern))
        )
    total = await session.scalar(select(func.count(Room.id)).where(*filters)) or 0
    records = await session.scalars(
        select(Room)
        .options(
            joinedload(Room.laboratory)
            .joinedload(Laboratory.department)
            .joinedload(Department.college)
        )
        .where(*filters)
        .order_by(Room.building_name, Room.room_number, Room.id)
        .offset((page - 1) * size)
        .limit(size)
    )
    return OrganizationPage(
        items=[_room_read(item) for item in records],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


async def get_room(session: AsyncSession, record_id: uuid.UUID) -> RoomRead:
    record = await session.scalar(
        select(Room)
        .options(
            joinedload(Room.laboratory)
            .joinedload(Laboratory.department)
            .joinedload(Department.college)
        )
        .where(Room.id == record_id)
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return _room_read(record)


async def create_room(session: AsyncSession, payload: RoomCreate) -> RoomRead:
    await _ensure_exists(session, Laboratory, payload.laboratory_id, "Laboratory")
    record = Room(**payload.model_dump())
    session.add(record)
    await _commit(session, "Room number already exists in this laboratory")
    return await get_room(session, record.id)


async def update_room(
    session: AsyncSession, record_id: uuid.UUID, payload: RoomUpdate
) -> RoomRead:
    record = await session.get(Room, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Room not found")
    changes = payload.model_dump(exclude_unset=True)
    if "laboratory_id" in changes:
        await _ensure_exists(session, Laboratory, changes["laboratory_id"], "Laboratory")
    for field, value in changes.items():
        setattr(record, field, value)
    await _commit(session, "Room number already exists in this laboratory")
    return await get_room(session, record_id)


async def delete_room(session: AsyncSession, record_id: uuid.UUID) -> None:
    await _delete(
        session,
        delete(Room).where(Room.id == record_id),
        missing_detail="Room not found",
        conflict_detail="Room is referenced by assets or transfers and cannot be deleted",
    )
    logger.info("hierarchy.room_deleted", extra={"room_id": str(record_id)})
