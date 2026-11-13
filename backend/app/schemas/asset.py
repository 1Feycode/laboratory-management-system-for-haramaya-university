from datetime import date, datetime
from typing import Annotated, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

AssetStatus = Literal[
    "OPERATIONAL",
    "UNDER_MAINTENANCE",
    "DEFECTIVE",
    "TRANSFER_PENDING",
    "DECOMMISSIONED",
]
T = TypeVar("T")


class AssetPage(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class CleanAssetText(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def trim_text_fields(cls, value):
        if isinstance(value, dict):
            return {
                key: item.strip() if isinstance(item, str) else item
                for key, item in value.items()
            }
        return value

    @model_validator(mode="after")
    def require_mutation(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        nullable_fields = {
            "legacy_tag_number",
            "purchase_date",
            "commissioning_date",
            "warranty_expiry_date",
        }
        for field in self.model_fields_set:
            if field not in nullable_fields and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class AssetCategoryCreate(CleanAssetText):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    requires_calibration: bool = False
    default_calibration_interval_days: Annotated[int, Field(ge=0)] = 0


class AssetCategoryUpdate(CleanAssetText):
    name: Annotated[str, Field(min_length=1, max_length=100)] | None = None
    requires_calibration: bool | None = None
    default_calibration_interval_days: Annotated[int, Field(ge=0)] | None = None


class AssetCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    requires_calibration: bool
    default_calibration_interval_days: int
    created_at: datetime


class AssetCreate(CleanAssetText):
    legacy_tag_number: Annotated[str, Field(max_length=100)] | None = None
    serial_number: Annotated[str, Field(min_length=1, max_length=100)]
    model_number: Annotated[str, Field(min_length=1, max_length=100)]
    manufacturer_name: Annotated[str, Field(min_length=1, max_length=150)]
    category_id: UUID
    laboratory_id: UUID
    room_id: UUID
    purchase_date: date | None = None
    commissioning_date: date | None = None
    warranty_expiry_date: date | None = None


class AssetUpdate(CleanAssetText):
    legacy_tag_number: Annotated[str, Field(max_length=100)] | None = None
    serial_number: Annotated[str, Field(min_length=1, max_length=100)] | None = None
    model_number: Annotated[str, Field(min_length=1, max_length=100)] | None = None
    manufacturer_name: Annotated[str, Field(min_length=1, max_length=150)] | None = None
    category_id: UUID | None = None
    purchase_date: date | None = None
    commissioning_date: date | None = None
    warranty_expiry_date: date | None = None


class AssetRead(BaseModel):
    id: UUID
    asset_code: str
    legacy_tag_number: str | None
    serial_number: str
    model_number: str
    manufacturer_name: str
    category_id: UUID
    category_name: str
    requires_calibration: bool
    default_calibration_interval_days: int
    laboratory_id: UUID
    laboratory_name: str
    room_id: UUID
    room_number: str
    building_name: str
    department_id: UUID
    department_name: str
    college_id: UUID
    college_name: str
    operational_status: AssetStatus
    purchase_date: date | None
    commissioning_date: date | None
    warranty_expiry_date: date | None
    last_calibrated_date: date | None
    next_calibration_due: date | None
    qr_code_url: str
    created_at: datetime
    updated_at: datetime
