from datetime import date, datetime
from typing import Annotated, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

T = TypeVar("T")


class CalibrationPage(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class CalibrationCreate(BaseModel):
    asset_id: UUID
    calibration_date: date
    standard_used: Annotated[str, Field(min_length=1, max_length=150)]
    certificate_reference: Annotated[str, Field(max_length=100)] | None = None
    accreditation_body: Annotated[str, Field(max_length=150)] | None = None
    passed: bool
    notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def trim_text_fields(cls, value):
        if isinstance(value, dict):
            return {
                key: item.strip() if isinstance(item, str) else item
                for key, item in value.items()
            }
        return value


class CalibrationRead(BaseModel):
    id: UUID
    asset_id: UUID
    asset_code: str
    technician_id: UUID
    technician_name: str
    calibration_date: date
    standard_used: str
    certificate_reference: str | None
    accreditation_body: str | None
    passed: bool
    next_due_date: date
    notes: str | None
    created_at: datetime


class CalibrationDueRead(BaseModel):
    asset_id: UUID
    asset_code: str
    model_number: str
    manufacturer_name: str
    category_name: str
    laboratory_name: str
    room_number: str
    last_calibrated_date: date | None
    next_calibration_due: date
    status: Literal["UPCOMING", "OVERDUE"]
