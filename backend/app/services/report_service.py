import csv
import io
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset, AssetCategory
from app.models.calibration import CalibrationLog
from app.models.maintenance import WorkOrder
from app.models.organization import College, Department, Laboratory, Room
from app.models.user import User
from app.schemas.reports import (
    CalibrationComplianceReport,
    CalibrationDueItem,
    CollegeMaintenanceSummary,
    CountByName,
    CriticalWorkOrderItem,
    DashboardReport,
    DowntimeReport,
)

REPORT_ROLES = {"ULMD_ADMIN", "LAB_MANAGER", "AUDITOR"}
ACTIVE_WORK_ORDER_STATUSES = {"OPEN", "ASSIGNED", "IN_PROGRESS"}
WORK_ORDER_STATUSES = (
    "OPEN",
    "ASSIGNED",
    "IN_PROGRESS",
    "AWAITING_PARTS",
    "AWAITING_APPROVAL",
    "RESOLVED",
    "CLOSED",
)


def _organization_joins(statement):
    return statement.join(Asset.laboratory).join(
        Laboratory.department
    ).join(Department.college)


def _scope_filters(
    user: User,
    *,
    college_id: UUID | None,
    department_id: UUID | None,
) -> list[Any]:
    if user.role.name not in REPORT_ROLES:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view operational reports",
        )

    filters: list[Any] = []
    if user.role.name == "LAB_MANAGER":
        filters.extend(
            [
                Laboratory.manager_id == user.id,
                Laboratory.department_id == user.department_id,
            ]
        )
    elif user.role.name == "AUDITOR" and user.department_id is not None:
        filters.append(Department.id == user.department_id)

    if college_id is not None:
        filters.append(College.id == college_id)
    if department_id is not None:
        filters.append(Department.id == department_id)
    return filters


def _date_window(
    date_from: date | None, date_to: date | None
) -> tuple[datetime, datetime] | None:
    if (date_from is None) != (date_to is None):
        raise HTTPException(
            status_code=422,
            detail="date_from and date_to must be provided together",
        )
    if date_from is None or date_to is None:
        return None
    if date_from > date_to:
        raise HTTPException(
            status_code=422,
            detail="date_from must be on or before date_to",
        )
    try:
        end_date = date_to + timedelta(days=1)
    except OverflowError as error:
        raise HTTPException(
            status_code=422, detail="date_to exceeds the supported date range"
        ) from error
    return (
        datetime.combine(date_from, time.min, tzinfo=timezone.utc),
        datetime.combine(end_date, time.min, tzinfo=timezone.utc),
    )


def _date_filters(
    column, window: tuple[datetime, datetime] | None
) -> list[Any]:
    if window is None:
        return []
    start, end = window
    return [column >= start, column < end]


def _calendar_date_filters(
    column,
    date_from: date | None,
    date_to: date | None,
) -> list[Any]:
    if date_from is None or date_to is None:
        return []
    try:
        end_date = date_to + timedelta(days=1)
    except OverflowError as error:
        raise HTTPException(
            status_code=422, detail="date_to exceeds the supported date range"
        ) from error
    return [column >= date_from, column < end_date]


def _work_order_base(filters: list[Any]):
    return (
        select(WorkOrder)
        .join(WorkOrder.asset)
        .join(Asset.laboratory)
        .join(Laboratory.department)
        .join(Department.college)
        .where(*filters)
    )


def _work_order_org_query(*columns):
    return (
        select(*columns)
        .select_from(WorkOrder)
        .join(WorkOrder.asset)
        .join(Asset.laboratory)
        .join(Laboratory.department)
        .join(Department.college)
    )


async def _asset_counts(
    session: AsyncSession, filters: list[Any]
) -> tuple[int, int, list[CountByName], list[CountByName]]:
    total = await session.scalar(
        _organization_joins(select(func.count(Asset.id))).where(*filters)
    ) or 0
    operational = await session.scalar(
        _organization_joins(
            select(func.count(Asset.id)).where(
                Asset.operational_status == "OPERATIONAL"
            )
        ).where(*filters)
    ) or 0
    category_rows = await session.execute(
        _organization_joins(
            select(AssetCategory.name, func.count(Asset.id))
            .join(Asset.category)
            .group_by(AssetCategory.name)
        ).where(*filters)
    )
    status_rows = await session.execute(
        _organization_joins(
            select(Asset.operational_status, func.count(Asset.id)).group_by(
                Asset.operational_status
            )
        ).where(*filters)
    )
    return (
        total,
        operational,
        [CountByName(name=name, count=count) for name, count in category_rows],
        [CountByName(name=name, count=count) for name, count in status_rows],
    )


async def _work_order_counts(
    session: AsyncSession,
    filters: list[Any],
    window: tuple[datetime, datetime] | None,
) -> tuple[int, int, list[CountByName], int]:
    created_filters = _date_filters(WorkOrder.created_at, window)
    status_rows = await session.execute(
        _work_order_base(filters + created_filters)
        .with_only_columns(WorkOrder.status, func.count(WorkOrder.id))
        .group_by(WorkOrder.status)
    )
    counts = {status: count for status, count in status_rows}
    total = sum(counts.values())
    active = await session.scalar(
        _work_order_base(
            filters + [WorkOrder.status.in_(ACTIVE_WORK_ORDER_STATUSES)]
        ).with_only_columns(func.count(WorkOrder.id))
    ) or 0

    completed_filters = [WorkOrder.closed_at.is_not(None)]
    if window is not None:
        completed_filters.extend(_date_filters(WorkOrder.closed_at, window))
    completed = await session.scalar(
        _work_order_base(filters + completed_filters)
        .with_only_columns(func.count(WorkOrder.id))
    ) or 0
    return (
        total,
        active,
        [CountByName(name=status, count=counts.get(status, 0)) for status in WORK_ORDER_STATUSES],
        completed,
    )


async def _calibration_counts(
    session: AsyncSession,
    filters: list[Any],
    date_from: date | None,
    date_to: date | None,
) -> tuple[int, int, int]:
    calibration_filters = _calendar_date_filters(
        CalibrationLog.calibration_date, date_from, date_to
    )
    query = (
        select(
            func.count(CalibrationLog.id),
            func.count(CalibrationLog.id).filter(CalibrationLog.passed.is_(True)),
            func.count(CalibrationLog.id).filter(CalibrationLog.passed.is_(False)),
        )
        .join(CalibrationLog.asset)
        .join(Asset.laboratory)
        .join(Laboratory.department)
        .join(Department.college)
        .where(*filters, *calibration_filters)
    )
    total, passed, failed = (await session.execute(query)).one()
    return total or 0, passed or 0, failed or 0


async def _calibration_due_items(
    session: AsyncSession,
    filters: list[Any],
    *,
    today: date,
    cutoff: date,
    overdue: bool,
    limit: int,
) -> list[CalibrationDueItem]:
    due_filter = (
        Asset.next_calibration_due < today
        if overdue
        else (Asset.next_calibration_due >= today)
        & (Asset.next_calibration_due <= cutoff)
    )
    rows = await session.execute(
        select(
            Asset.id,
            Asset.asset_code,
            Asset.model_number,
            Asset.next_calibration_due,
            AssetCategory.name,
            College.name,
            Department.name,
            Laboratory.name,
            Room.room_number,
        )
        .join(Asset.category)
        .join(Asset.laboratory)
        .join(Laboratory.department)
        .join(Department.college)
        .join(Asset.room)
        .where(
            *filters,
            AssetCategory.requires_calibration.is_(True),
            Asset.next_calibration_due.is_not(None),
            due_filter,
        )
        .order_by(Asset.next_calibration_due, Asset.asset_code, Asset.id)
        .limit(limit)
    )
    return [
        CalibrationDueItem(
            asset_id=row[0],
            asset_code=row[1],
            model_number=row[2],
            next_calibration_due=row[3],
            category_name=row[4],
            college_name=row[5],
            department_name=row[6],
            laboratory_name=row[7],
            room_number=row[8],
            status="OVERDUE" if overdue else "UPCOMING",
        )
        for row in rows
    ]


async def _calibration_due_counts(
    session: AsyncSession,
    filters: list[Any],
    *,
    today: date,
    cutoff: date,
) -> tuple[int, int]:
    base = (
        select(func.count(Asset.id))
        .join(Asset.category)
        .join(Asset.laboratory)
        .join(Laboratory.department)
        .join(Department.college)
        .where(
            *filters,
            AssetCategory.requires_calibration.is_(True),
            Asset.next_calibration_due.is_not(None),
        )
    )
    overdue = await session.scalar(
        base.where(Asset.next_calibration_due < today)
    ) or 0
    upcoming = await session.scalar(
        base.where(
            Asset.next_calibration_due >= today,
            Asset.next_calibration_due <= cutoff,
        )
    ) or 0
    return overdue, upcoming


async def _critical_work_orders(
    session: AsyncSession, filters: list[Any], limit: int = 10
) -> list[CriticalWorkOrderItem]:
    rows = await session.execute(
        select(
            WorkOrder.id,
            WorkOrder.ticket_number,
            Asset.asset_code,
            College.name,
            Department.name,
            Laboratory.name,
            WorkOrder.severity,
            WorkOrder.status,
            WorkOrder.created_at,
        )
        .join(WorkOrder.asset)
        .join(Asset.laboratory)
        .join(Laboratory.department)
        .join(Department.college)
        .where(
            *filters,
            WorkOrder.severity == "CRITICAL",
            WorkOrder.status != "CLOSED",
        )
        .order_by(WorkOrder.created_at, WorkOrder.id)
        .limit(limit)
    )
    return [
        CriticalWorkOrderItem(
            id=row[0],
            ticket_number=row[1],
            asset_code=row[2],
            college_name=row[3],
            department_name=row[4],
            laboratory_name=row[5],
            severity=row[6],
            status=row[7],
            created_at=row[8],
        )
        for row in rows
    ]


async def get_dashboard(
    session: AsyncSession,
    user: User,
    *,
    college_id: UUID | None,
    department_id: UUID | None,
    date_from: date | None,
    date_to: date | None,
    within_days: int,
) -> DashboardReport:
    filters = _scope_filters(
        user, college_id=college_id, department_id=department_id
    )
    window = _date_window(date_from, date_to)
    try:
        cutoff = datetime.now(timezone.utc).date() + timedelta(days=within_days)
    except OverflowError as error:
        raise HTTPException(
            status_code=422, detail="within_days exceeds the supported date range"
        ) from error

    asset_total, operational_assets, categories, statuses = await _asset_counts(
        session, filters
    )
    work_total, active_work_orders, work_statuses, work_completed = (
        await _work_order_counts(session, filters, window)
    )
    calibration_total, calibrations_passed, calibrations_failed = (
        await _calibration_counts(
            session, filters, date_from=date_from, date_to=date_to
        )
    )
    overdue_count, upcoming_count = await _calibration_due_counts(
        session, filters, today=datetime.now(timezone.utc).date(), cutoff=cutoff
    )
    overdue_items = await _calibration_due_items(
        session,
        filters,
        today=datetime.now(timezone.utc).date(),
        cutoff=cutoff,
        overdue=True,
        limit=10,
    )
    upcoming_items = await _calibration_due_items(
        session,
        filters,
        today=datetime.now(timezone.utc).date(),
        cutoff=cutoff,
        overdue=False,
        limit=10,
    )
    critical_orders = await _critical_work_orders(session, filters)

    return DashboardReport(
        asset_total=asset_total,
        operational_assets=operational_assets,
        assets_by_category=categories,
        assets_by_status=statuses,
        work_order_total=work_total,
        active_work_orders=active_work_orders,
        work_orders_completed=work_completed,
        work_orders_by_status=work_statuses,
        calibration_records=calibration_total,
        calibrations_passed=calibrations_passed,
        calibrations_failed=calibrations_failed,
        overdue_calibrations=overdue_count,
        upcoming_calibrations=upcoming_count,
        upcoming_calibration_items=upcoming_items,
        overdue_calibration_items=overdue_items,
        critical_work_orders=critical_orders,
        availability_status="PENDING_APPROVED_DEFINITION",
        uptime_percentage=None,
        downtime_asset_hours=None,
    )


async def get_downtime_report(
    session: AsyncSession,
    user: User,
    *,
    college_id: UUID | None,
    department_id: UUID | None,
    date_from: date,
    date_to: date,
) -> DowntimeReport:
    filters = _scope_filters(
        user, college_id=college_id, department_id=department_id
    )
    window = _date_window(date_from, date_to)
    if window is None:
        raise HTTPException(status_code=422, detail="A date range is required")
    start, end = window

    asset_total = await session.scalar(
        _organization_joins(select(func.count(Asset.id))).where(*filters)
    ) or 0

    actual_end = min(end, datetime.now(timezone.utc))
    status_counts: dict[str, int] = defaultdict(int)
    college_stats: dict[UUID, dict[str, Any]] = {}
    request_count = 0
    completed_count = 0
    active_count = 0

    def college_stat(college_id: UUID, college_name: str) -> dict[str, Any]:
        return college_stats.setdefault(
            college_id,
            {"name": college_name, "requests": 0, "completed": 0, "active": 0},
        )

    request_rows = await session.execute(
        _work_order_org_query(
            College.id,
            College.name,
            WorkOrder.status,
            func.count(WorkOrder.id),
        )
        .where(
            *filters,
            WorkOrder.created_at >= start,
            WorkOrder.created_at < actual_end,
        )
        .group_by(College.id, College.name, WorkOrder.status)
    )
    for college_id, college_name, status, count in request_rows:
        college_stat(college_id, college_name)["requests"] += count
        request_count += count
        status_counts[status] += count

    completed_rows = await session.execute(
        _work_order_org_query(
            College.id,
            College.name,
            func.count(WorkOrder.id),
        )
        .where(
            *filters,
            WorkOrder.closed_at >= start,
            WorkOrder.closed_at < actual_end,
        )
        .group_by(College.id, College.name)
    )
    for college_id, college_name, count in completed_rows:
        college_stat(college_id, college_name)["completed"] += count
        completed_count += count

    active_rows = await session.execute(
        _work_order_org_query(
            College.id,
            College.name,
            func.count(WorkOrder.id),
        )
        .where(
            *filters,
            WorkOrder.status.in_(ACTIVE_WORK_ORDER_STATUSES),
            WorkOrder.created_at < actual_end,
        )
        .group_by(College.id, College.name)
    )
    for college_id, college_name, count in active_rows:
        college_stat(college_id, college_name)["active"] += count
        active_count += count

    by_college = [
        CollegeMaintenanceSummary(
            college_id=college_id,
            college_name=stats["name"],
            work_order_requests=stats["requests"],
            work_orders_completed=stats["completed"],
            active_work_orders=stats["active"],
        )
        for college_id, stats in sorted(
            college_stats.items(), key=lambda item: item[1]["name"].casefold()
        )
    ]

    return DowntimeReport(
        date_from=date_from,
        date_to=date_to,
        availability_status="PENDING_APPROVED_DEFINITION",
        asset_total=asset_total,
        uptime_percentage=None,
        downtime_asset_hours=None,
        work_order_requests=request_count,
        work_orders_completed=completed_count,
        active_work_orders=active_count,
        work_orders_by_status=[
            CountByName(name=status, count=status_counts.get(status, 0))
            for status in WORK_ORDER_STATUSES
        ],
        by_college=by_college,
    )


async def get_calibration_compliance(
    session: AsyncSession,
    user: User,
    *,
    college_id: UUID | None,
    department_id: UUID | None,
    date_from: date | None,
    date_to: date | None,
    within_days: int,
) -> CalibrationComplianceReport:
    filters = _scope_filters(
        user, college_id=college_id, department_id=department_id
    )
    _date_window(date_from, date_to)
    try:
        today = datetime.now(timezone.utc).date()
        cutoff = today + timedelta(days=within_days)
    except OverflowError as error:
        raise HTTPException(
            status_code=422, detail="within_days exceeds the supported date range"
        ) from error

    assets_requiring_calibration = await session.scalar(
        _organization_joins(
            select(func.count(Asset.id)).join(Asset.category)
        ).where(*filters, AssetCategory.requires_calibration.is_(True))
    ) or 0
    overdue, upcoming = await _calibration_due_counts(
        session, filters, today=today, cutoff=cutoff
    )
    total, passed, failed = await _calibration_counts(
        session, filters, date_from=date_from, date_to=date_to
    )
    overdue_items = await _calibration_due_items(
        session, filters, today=today, cutoff=cutoff, overdue=True, limit=100
    )
    upcoming_items = await _calibration_due_items(
        session, filters, today=today, cutoff=cutoff, overdue=False, limit=100
    )
    return CalibrationComplianceReport(
        assets_requiring_calibration=assets_requiring_calibration,
        overdue_calibrations=overdue,
        upcoming_calibrations=upcoming,
        calibration_records=total,
        calibrations_passed=passed,
        calibrations_failed=failed,
        overdue_items=overdue_items,
        upcoming_items=upcoming_items,
    )


def _csv_cell(value: Any) -> Any:
    if isinstance(value, str):
        if value.startswith(("\t", "\r", "\n")) or value.lstrip(
            " \t\r\n"
        ).startswith(("=", "+", "-", "@")):
            return "'" + value
    return value


async def export_inventory_csv(
    session: AsyncSession,
    user: User,
    *,
    college_id: UUID | None,
    department_id: UUID | None,
    status: str | None,
    date_from: date | None,
    date_to: date | None,
) -> bytes:
    filters = _scope_filters(
        user, college_id=college_id, department_id=department_id
    )
    window = _date_window(date_from, date_to)
    if status is not None:
        filters.append(Asset.operational_status == status)
    filters.extend(_date_filters(Asset.created_at, window))
    rows = await session.execute(
        _organization_joins(
            select(
                Asset.asset_code,
                Asset.serial_number,
                Asset.manufacturer_name,
                Asset.model_number,
                AssetCategory.name,
                College.name,
                Department.name,
                Laboratory.name,
                Room.room_number,
                Asset.operational_status,
                Asset.purchase_date,
                Asset.commissioning_date,
                Asset.warranty_expiry_date,
                Asset.last_calibrated_date,
                Asset.next_calibration_due,
                Asset.created_at,
            )
            .join(Asset.category)
            .join(Asset.room)
        )
        .where(*filters)
        .order_by(Asset.asset_code, Asset.id)
    )
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        [
            "Asset Code",
            "Serial Number",
            "Manufacturer",
            "Model",
            "Category",
            "College",
            "Department",
            "Laboratory",
            "Room",
            "Operational Status",
            "Purchase Date",
            "Commissioning Date",
            "Warranty Expiry Date",
            "Last Calibrated Date",
            "Next Calibration Due",
            "Registered At",
        ]
    )
    for row in rows:
        writer.writerow([_csv_cell(value) for value in row])
    return output.getvalue().encode("utf-8-sig")
