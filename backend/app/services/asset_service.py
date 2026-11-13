import logging
import math
import uuid
from datetime import datetime, timezone
from io import BytesIO
from typing import Literal
from urllib.parse import quote

import qrcode
from fastapi import HTTPException, Response
from qrcode.constants import ERROR_CORRECT_H
from qrcode.image.svg import SvgPathImage
from sqlalchemy import desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import get_settings
from app.models.asset import Asset, AssetAuditLog, AssetCategory
from app.models.organization import College, Department, Laboratory, Room
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

logger = logging.getLogger(__name__)
AssetSortField = Literal[
    "asset_code",
    "created_at",
    "model_number",
    "operational_status",
    "purchase_date",
]


async def _commit(session: AsyncSession, detail: str) -> None:
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail=detail) from None


async def _flush(session: AsyncSession, detail: str) -> None:
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail=detail) from None


def _asset_query():
    return (
        select(Asset)
        .options(
            joinedload(Asset.category),
            joinedload(Asset.laboratory)
            .joinedload(Laboratory.department)
            .joinedload(Department.college),
            joinedload(Asset.room),
        )
        .join(Asset.laboratory)
        .join(Laboratory.department)
    )


def _asset_read(asset: Asset) -> AssetRead:
    return AssetRead(
        id=asset.id,
        asset_code=asset.asset_code,
        legacy_tag_number=asset.legacy_tag_number,
        serial_number=asset.serial_number,
        model_number=asset.model_number,
        manufacturer_name=asset.manufacturer_name,
        category_id=asset.category_id,
        category_name=asset.category.name,
        requires_calibration=asset.category.requires_calibration,
        default_calibration_interval_days=asset.category.default_calibration_interval_days,
        laboratory_id=asset.laboratory_id,
        laboratory_name=asset.laboratory.name,
        room_id=asset.room_id,
        room_number=asset.room.room_number,
        building_name=asset.room.building_name,
        department_id=asset.laboratory.department_id,
        department_name=asset.laboratory.department.name,
        college_id=asset.laboratory.department.college.id,
        college_name=asset.laboratory.department.college.name,
        operational_status=asset.operational_status,
        purchase_date=asset.purchase_date,
        commissioning_date=asset.commissioning_date,
        warranty_expiry_date=asset.warranty_expiry_date,
        last_calibrated_date=asset.last_calibrated_date,
        next_calibration_due=asset.next_calibration_due,
        qr_code_url=asset.qr_code_path or f"/api/v1/assets/{asset.id}/qr",
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


def _asset_values(asset: Asset) -> dict[str, str | None]:
    return {
        "asset_code": asset.asset_code,
        "legacy_tag_number": asset.legacy_tag_number,
        "serial_number": asset.serial_number,
        "model_number": asset.model_number,
        "manufacturer_name": asset.manufacturer_name,
        "category_id": str(asset.category_id),
        "laboratory_id": str(asset.laboratory_id),
        "room_id": str(asset.room_id),
        "operational_status": asset.operational_status,
        "purchase_date": asset.purchase_date.isoformat() if asset.purchase_date else None,
        "commissioning_date": (
            asset.commissioning_date.isoformat() if asset.commissioning_date else None
        ),
        "warranty_expiry_date": (
            asset.warranty_expiry_date.isoformat()
            if asset.warranty_expiry_date
            else None
        ),
        "last_calibrated_date": (
            asset.last_calibrated_date.isoformat()
            if asset.last_calibrated_date
            else None
        ),
        "next_calibration_due": (
            asset.next_calibration_due.isoformat()
            if asset.next_calibration_due
            else None
        ),
        "qr_code_path": asset.qr_code_path,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
        "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
    }


def _category_values(
    category: AssetCategory,
) -> dict[str, str | int | bool | None]:
    return {
        "name": category.name,
        "requires_calibration": category.requires_calibration,
        "default_calibration_interval_days": (
            category.default_calibration_interval_days
        ),
        "created_at": category.created_at.isoformat() if category.created_at else None,
    }


async def list_categories(
    session: AsyncSession, *, page: int, size: int, search: str | None
) -> AssetPage[AssetCategoryRead]:
    filters = []
    if search:
        filters.append(AssetCategory.name.ilike(f"%{search.strip()}%"))
    total = await session.scalar(
        select(func.count(AssetCategory.id)).where(*filters)
    ) or 0
    records = await session.scalars(
        select(AssetCategory)
        .where(*filters)
        .order_by(AssetCategory.name, AssetCategory.id)
        .offset((page - 1) * size)
        .limit(size)
    )
    return AssetPage(
        items=[AssetCategoryRead.model_validate(item) for item in records],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


async def get_category(
    session: AsyncSession, category_id: uuid.UUID
) -> AssetCategoryRead:
    category = await session.get(AssetCategory, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Asset category not found")
    return AssetCategoryRead.model_validate(category)


async def create_category(
    session: AsyncSession,
    payload: AssetCategoryCreate,
    user: User,
    ip_address: str | None,
) -> AssetCategoryRead:
    category = AssetCategory(**payload.model_dump())
    session.add(category)
    await _flush(session, "An asset category with this name already exists")
    session.add(
        AssetAuditLog(
            user_id=user.id,
            action="ASSET_CATEGORY_CREATED",
            entity_type="asset_categories",
            entity_id=str(category.id),
            old_values=None,
            new_values=_category_values(category),
            ip_address=ip_address,
        )
    )
    await _commit(session, "An asset category with this name already exists")
    await session.refresh(category)
    return AssetCategoryRead.model_validate(category)


async def update_category(
    session: AsyncSession,
    category_id: uuid.UUID,
    payload: AssetCategoryUpdate,
    user: User,
    ip_address: str | None,
) -> AssetCategoryRead:
    category = await session.get(AssetCategory, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Asset category not found")
    old_values = _category_values(category)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    session.add(
        AssetAuditLog(
            user_id=user.id,
            action="ASSET_CATEGORY_UPDATED",
            entity_type="asset_categories",
            entity_id=str(category.id),
            old_values=old_values,
            new_values=_category_values(category),
            ip_address=ip_address,
        )
    )
    await _commit(session, "An asset category with this name already exists")
    await session.refresh(category)
    return AssetCategoryRead.model_validate(category)


async def delete_category(
    session: AsyncSession,
    category_id: uuid.UUID,
    user: User,
    ip_address: str | None,
) -> None:
    category = await session.get(AssetCategory, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Asset category not found")
    try:
        old_values = _category_values(category)
        await session.delete(category)
        session.add(
            AssetAuditLog(
                user_id=user.id,
                action="ASSET_CATEGORY_DELETED",
                entity_type="asset_categories",
                entity_id=str(category.id),
                old_values=old_values,
                new_values=None,
                ip_address=ip_address,
            )
        )
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="This category is used by assets and cannot be deleted",
        ) from None


async def _asset_category(
    session: AsyncSession, category_id: uuid.UUID
) -> AssetCategory:
    category = await session.get(AssetCategory, category_id)
    if category is None:
        raise HTTPException(status_code=422, detail="Asset category does not exist")
    return category


async def _validate_location(
    session: AsyncSession,
    laboratory_id: uuid.UUID,
    room_id: uuid.UUID,
    *,
    lock_department: bool = False,
) -> tuple[Laboratory, Department, College]:
    laboratory = await session.scalar(
        select(Laboratory)
        .where(Laboratory.id == laboratory_id)
        .with_for_update()
    )
    if laboratory is None:
        raise HTTPException(status_code=422, detail="Laboratory does not exist")
    room = await session.scalar(
        select(Room).where(Room.id == room_id).with_for_update()
    )
    if room is None:
        raise HTTPException(status_code=422, detail="Room does not exist")
    if room.laboratory_id != laboratory.id:
        raise HTTPException(
            status_code=422,
            detail="Room must belong to the selected custodian laboratory",
        )
    department_query = select(Department).where(
        Department.id == laboratory.department_id
    )
    if lock_department:
        department_query = department_query.with_for_update()
    department = await session.scalar(department_query)
    if department is None:
        raise HTTPException(status_code=422, detail="Laboratory department does not exist")
    college = await session.scalar(
        select(College)
        .where(College.id == department.college_id)
        .with_for_update()
    )
    if college is None:
        raise HTTPException(status_code=422, detail="Department college does not exist")
    return laboratory, department, college


def _authorize_lab_write(user: User, laboratory: Laboratory) -> None:
    if user.role.name == "ULMD_ADMIN":
        return
    if user.role.name != "LAB_MANAGER":
        raise HTTPException(status_code=403, detail="You cannot manage laboratory assets")
    if user.department_id != laboratory.department_id:
        raise HTTPException(status_code=403, detail="You cannot manage assets outside your department")
    if laboratory.manager_id != user.id:
        raise HTTPException(status_code=403, detail="You are not assigned to manage this laboratory")


async def _next_asset_code(
    session: AsyncSession, department: Department, college: College
) -> str:
    prefix = f"HU-{college.code}-{department.code}-"
    latest = await session.scalar(
        select(Asset.asset_code)
        .where(func.left(Asset.asset_code, len(prefix)) == prefix)
        .order_by(Asset.asset_code.desc())
        .limit(1)
    )
    sequence = int(latest.rsplit("-", 1)[1]) + 1 if latest else 1
    if sequence > 9999:
        raise HTTPException(
            status_code=409,
            detail="This department has reached the approved four-digit asset-code limit",
        )
    return f"{prefix}{sequence:04d}"


async def create_asset(
    session: AsyncSession,
    payload: AssetCreate,
    user: User,
    ip_address: str | None,
) -> AssetRead:
    await _asset_category(session, payload.category_id)
    laboratory, department, college = await _validate_location(
        session, payload.laboratory_id, payload.room_id, lock_department=True
    )
    _authorize_lab_write(user, laboratory)
    asset = Asset(
        **payload.model_dump(),
        asset_code=await _next_asset_code(session, department, college),
        operational_status="OPERATIONAL",
    )
    session.add(asset)
    await _flush(
        session,
        "The manufacturer serial number is already registered or the asset code conflicts",
    )
    asset.qr_code_path = f"/api/v1/assets/{asset.id}/qr"
    session.add(
        AssetAuditLog(
            user_id=user.id,
            action="ASSET_CREATED",
            entity_type="assets",
            entity_id=str(asset.id),
            old_values=None,
            new_values=_asset_values(asset),
            ip_address=ip_address,
        )
    )
    await _commit(
        session,
        "The manufacturer serial number is already registered or the asset code conflicts",
    )
    logger.info(
        "assets.created",
        extra={"asset_id": str(asset.id), "asset_code": asset.asset_code},
    )
    return await get_asset(session, asset.id)


async def list_assets(
    session: AsyncSession,
    *,
    page: int,
    size: int,
    search: str | None,
    college_id: uuid.UUID | None,
    department_id: uuid.UUID | None,
    laboratory_id: uuid.UUID | None,
    category_id: uuid.UUID | None,
    operational_status: AssetStatus | None,
    sort_by: AssetSortField,
    sort_order: Literal["asc", "desc"],
) -> AssetPage[AssetRead]:
    filters = []
    if college_id:
        filters.append(Department.college_id == college_id)
    if department_id:
        filters.append(Laboratory.department_id == department_id)
    if laboratory_id:
        filters.append(Asset.laboratory_id == laboratory_id)
    if category_id:
        filters.append(Asset.category_id == category_id)
    if operational_status:
        filters.append(Asset.operational_status == operational_status)
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                Asset.asset_code.ilike(pattern),
                Asset.legacy_tag_number.ilike(pattern),
                Asset.serial_number.ilike(pattern),
                Asset.model_number.ilike(pattern),
                Asset.manufacturer_name.ilike(pattern),
            )
        )
    total = await session.scalar(
        select(func.count(Asset.id))
        .join(Asset.laboratory)
        .join(Laboratory.department)
        .where(*filters)
    ) or 0
    sort_column = {
        "asset_code": Asset.asset_code,
        "created_at": Asset.created_at,
        "model_number": Asset.model_number,
        "operational_status": Asset.operational_status,
        "purchase_date": Asset.purchase_date,
    }[sort_by]
    sort_expression = sort_column.asc() if sort_order == "asc" else desc(sort_column)
    records = await session.scalars(
        _asset_query()
        .where(*filters)
        .order_by(sort_expression, Asset.id)
        .offset((page - 1) * size)
        .limit(size)
    )
    return AssetPage(
        items=[_asset_read(item) for item in records],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


async def get_asset(session: AsyncSession, asset_id: uuid.UUID) -> AssetRead:
    asset = await session.scalar(_asset_query().where(Asset.id == asset_id))
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return _asset_read(asset)


async def get_asset_by_code(session: AsyncSession, asset_code: str) -> AssetRead:
    identifier = asset_code.strip()
    asset = await session.scalar(
        _asset_query().where(Asset.asset_code == identifier)
    )
    if asset is not None:
        return _asset_read(asset)
    legacy_matches = list(
        (
            await session.scalars(
                _asset_query()
                .where(Asset.legacy_tag_number == identifier)
                .limit(2)
            )
        ).all()
    )
    if not legacy_matches:
        raise HTTPException(status_code=404, detail="Asset code or legacy tag not found")
    if len(legacy_matches) > 1:
        raise HTTPException(
            status_code=409,
            detail="Legacy tag matches multiple assets; use the universal asset code",
        )
    return _asset_read(legacy_matches[0])


async def update_asset(
    session: AsyncSession,
    asset_id: uuid.UUID,
    payload: AssetUpdate,
    user: User,
    ip_address: str | None,
) -> AssetRead:
    asset = await session.scalar(
        select(Asset)
        .options(joinedload(Asset.laboratory))
        .where(Asset.id == asset_id)
        .with_for_update(of=Asset)
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    if asset.operational_status == "TRANSFER_PENDING":
        raise HTTPException(
            status_code=409,
            detail="Asset details are locked while a custody transfer is pending",
        )
    _authorize_lab_write(user, asset.laboratory)
    old_values = _asset_values(asset)
    changes = payload.model_dump(exclude_unset=True)
    if "category_id" in changes:
        await _asset_category(session, changes["category_id"])
    for field, value in changes.items():
        setattr(asset, field, value)
    asset.updated_at = datetime.now(timezone.utc)
    session.add(
        AssetAuditLog(
            user_id=user.id,
            action="ASSET_UPDATED",
            entity_type="assets",
            entity_id=str(asset.id),
            old_values=old_values,
            new_values=_asset_values(asset),
            ip_address=ip_address,
        )
    )
    await _commit(
        session,
        "The manufacturer serial number is already registered by another asset",
    )
    logger.info("assets.updated", extra={"asset_id": str(asset.id)})
    return await get_asset(session, asset.id)


def build_asset_qr_payload(
    asset_code: str, public_base_url: str | None
) -> str:
    if not public_base_url:
        return asset_code
    return (
        f"{public_base_url.rstrip('/')}/assets/scan"
        f"?code={quote(asset_code, safe='')}"
    )


def render_qr_svg(
    asset_code: str, public_base_url: str | None = None
) -> bytes:
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,
        box_size=8,
        border=4,
    )
    qr.add_data(build_asset_qr_payload(asset_code, public_base_url))
    qr.make(fit=True)
    image = qr.make_image(image_factory=SvgPathImage)
    output = BytesIO()
    image.save(output)
    return output.getvalue()


async def get_asset_qr(session: AsyncSession, asset_id: uuid.UUID) -> Response:
    asset = await session.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    public_base_url = get_settings().asset_public_base_url
    return Response(
        content=render_qr_svg(
            asset.asset_code,
            str(public_base_url) if public_base_url is not None else None,
        ),
        media_type="image/svg+xml",
        headers={"Cache-Control": "private, max-age=300"},
    )
