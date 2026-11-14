import logging
import math
import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.asset import Asset, AssetAuditLog, AssetCategory
from app.models.calibration import CalibrationLog
from app.models.user import User
from app.schemas.calibration import (
    CalibrationCreate,
    CalibrationDueRead,
    CalibrationPage,
    CalibrationRead,
)

logger = logging.getLogger(__name__)


async def _commit(session: AsyncSession, detail: str) -> None:
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail=detail) from None


def _calibration_query():
    return select(CalibrationLog).options(
        joinedload(CalibrationLog.asset).joinedload(Asset.category),
        joinedload(CalibrationLog.technician),
    )


def _calibration_read(log: CalibrationLog) -> CalibrationRead:
    return CalibrationRead(
        id=log.id,
        asset_id=log.asset_id,
        asset_code=log.asset.asset_code,
        technician_id=log.technician_id,
        technician_name=log.technician.full_name,
        calibration_date=log.calibration_date,
        standard_used=log.standard_used,
        certificate_reference=log.certificate_reference,
        accreditation_body=log.accreditation_body,
        passed=log.passed,
        next_due_date=log.next_due_date,
        notes=log.notes,
        created_at=log.created_at,
    )


def _asset_calibration_values(asset: Asset) -> dict[str, str | None]:
    return {
        "asset_code": asset.asset_code,
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
        "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
    }


async def list_calibrations(
    session: AsyncSession,
    *,
    page: int,
    size: int,
    asset_id: uuid.UUID | None,
) -> CalibrationPage[CalibrationRead]:
    filters = [CalibrationLog.asset_id == asset_id] if asset_id else []
    total = (
        await session.scalar(
            select(func.count(CalibrationLog.id)).where(*filters)
        )
        or 0
    )
    records = await session.scalars(
        _calibration_query()
        .where(*filters)
        .order_by(
            CalibrationLog.calibration_date.desc(),
            CalibrationLog.created_at.desc(),
            CalibrationLog.id.desc(),
        )
        .offset((page - 1) * size)
        .limit(size)
    )
    return CalibrationPage(
        items=[_calibration_read(log) for log in records],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


async def list_due_calibrations(
    session: AsyncSession,
    *,
    within_days: int,
    page: int,
    size: int,
) -> CalibrationPage[CalibrationDueRead]:
    today = datetime.now(timezone.utc).date()
    try:
        cutoff = today + timedelta(days=within_days)
    except OverflowError as error:
        raise HTTPException(
            status_code=422,
            detail="within_days exceeds the supported date range",
        ) from error
    filters = (
        AssetCategory.requires_calibration.is_(True),
        Asset.next_calibration_due.is_not(None),
        Asset.next_calibration_due <= cutoff,
    )
    total = (
        await session.scalar(
            select(func.count(Asset.id))
            .join(Asset.category)
            .where(*filters)
        )
        or 0
    )
    records = await session.scalars(
        select(Asset)
        .options(
            joinedload(Asset.category),
            joinedload(Asset.laboratory),
            joinedload(Asset.room),
        )
        .join(Asset.category)
        .where(*filters)
        .order_by(Asset.next_calibration_due, Asset.asset_code, Asset.id)
        .offset((page - 1) * size)
        .limit(size)
    )
    items = [
        CalibrationDueRead(
            asset_id=asset.id,
            asset_code=asset.asset_code,
            model_number=asset.model_number,
            manufacturer_name=asset.manufacturer_name,
            category_name=asset.category.name,
            laboratory_name=asset.laboratory.name,
            room_number=asset.room.room_number,
            last_calibrated_date=asset.last_calibrated_date,
            next_calibration_due=asset.next_calibration_due,
            status=(
                "OVERDUE"
                if asset.next_calibration_due < today
                else "UPCOMING"
            ),
        )
        for asset in records
    ]
    return CalibrationPage(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


async def create_calibration(
    session: AsyncSession,
    payload: CalibrationCreate,
    user: User,
    ip_address: str | None,
) -> CalibrationRead:
    asset = await session.scalar(
        select(Asset)
        .options(joinedload(Asset.category))
        .where(Asset.id == payload.asset_id)
        .with_for_update(of=Asset)
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    if not asset.category.requires_calibration:
        raise HTTPException(
            status_code=409,
            detail="The asset category is not marked as requiring calibration",
        )
    interval_days = asset.category.default_calibration_interval_days
    if interval_days <= 0:
        raise HTTPException(
            status_code=409,
            detail="A positive default calibration interval is required for this category",
        )

    next_due_date = payload.calibration_date + timedelta(days=interval_days)
    old_asset_values = _asset_calibration_values(asset)
    asset.last_calibrated_date = payload.calibration_date
    if payload.passed:
        asset.next_calibration_due = next_due_date
    asset.updated_at = datetime.now(timezone.utc)
    log = CalibrationLog(
        asset_id=asset.id,
        technician_id=user.id,
        calibration_date=payload.calibration_date,
        standard_used=payload.standard_used,
        certificate_reference=payload.certificate_reference or None,
        accreditation_body=payload.accreditation_body or None,
        passed=payload.passed,
        next_due_date=next_due_date,
        notes=payload.notes or None,
    )
    session.add(log)
    await session.flush()
    session.add_all(
        [
            AssetAuditLog(
                user_id=user.id,
                action="CALIBRATION_LOGGED",
                entity_type="calibration_logs",
                entity_id=str(log.id),
                old_values=None,
                new_values={
                    "asset_id": str(log.asset_id),
                    "technician_id": str(log.technician_id),
                    "calibration_date": log.calibration_date.isoformat(),
                    "standard_used": log.standard_used,
                    "certificate_reference": log.certificate_reference,
                    "accreditation_body": log.accreditation_body,
                    "passed": log.passed,
                    "next_due_date": log.next_due_date.isoformat(),
                    "notes": log.notes,
                },
                ip_address=ip_address,
            ),
            AssetAuditLog(
                user_id=user.id,
                action="ASSET_CALIBRATION_UPDATED",
                entity_type="assets",
                entity_id=str(asset.id),
                old_values=old_asset_values,
                new_values=_asset_calibration_values(asset),
                ip_address=ip_address,
            ),
        ]
    )
    await _commit(session, "Calibration record could not be saved")
    logger.info(
        "calibration.record_created",
        extra={
            "asset_id": str(asset.id),
            "calibration_id": str(log.id),
            "passed": log.passed,
        },
    )
    saved = await session.scalar(
        _calibration_query().where(CalibrationLog.id == log.id)
    )
    if saved is None:
        raise HTTPException(
            status_code=500, detail="Saved calibration record could not be reloaded"
        )
    return _calibration_read(saved)
