from datetime import datetime
from typing import Annotated, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

LabType = Literal["WET", "DRY", "COMPUTING", "WORKSHOP"]
T = TypeVar("T")


class OrganizationPage(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class CleanTextModel(BaseModel):
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
        for field in self.model_fields_set:
            if field != "manager_id" and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class CollegeCreate(CleanTextModel):
    name: Annotated[str, Field(min_length=1, max_length=150)]
    code: Annotated[str, Field(min_length=1, max_length=20)]


class CollegeUpdate(CleanTextModel):
    name: Annotated[str, Field(min_length=1, max_length=150)] | None = None
    code: Annotated[str, Field(min_length=1, max_length=20)] | None = None


class CollegeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    created_at: datetime


class DepartmentCreate(CleanTextModel):
    college_id: UUID
    name: Annotated[str, Field(min_length=1, max_length=150)]
    code: Annotated[str, Field(min_length=1, max_length=20)]


class DepartmentUpdate(CleanTextModel):
    college_id: UUID | None = None
    name: Annotated[str, Field(min_length=1, max_length=150)] | None = None
    code: Annotated[str, Field(min_length=1, max_length=20)] | None = None


class DepartmentRead(BaseModel):
    id: UUID
    college_id: UUID
    college_name: str
    name: str
    code: str
    created_at: datetime


class LaboratoryCreate(CleanTextModel):
    department_id: UUID
    name: Annotated[str, Field(min_length=1, max_length=150)]
    lab_type: LabType
    manager_id: UUID | None = None


class LaboratoryUpdate(CleanTextModel):
    department_id: UUID | None = None
    name: Annotated[str, Field(min_length=1, max_length=150)] | None = None
    lab_type: LabType | None = None
    manager_id: UUID | None = None


class LaboratoryRead(BaseModel):
    id: UUID
    department_id: UUID
    department_name: str
    college_name: str
    name: str
    lab_type: LabType
    manager_id: UUID | None
    manager_name: str | None
    created_at: datetime


class RoomCreate(CleanTextModel):
    laboratory_id: UUID
    room_number: Annotated[str, Field(min_length=1, max_length=50)]
    building_name: Annotated[str, Field(min_length=1, max_length=150)]


class RoomUpdate(CleanTextModel):
    laboratory_id: UUID | None = None
    room_number: Annotated[str, Field(min_length=1, max_length=50)] | None = None
    building_name: Annotated[str, Field(min_length=1, max_length=150)] | None = None


class RoomRead(BaseModel):
    id: UUID
    laboratory_id: UUID
    laboratory_name: str
    department_name: str
    college_name: str
    room_number: str
    building_name: str
    created_at: datetime
