from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)

RoleName = Literal[
    "ULMD_ADMIN",
    "MAINTENANCE_TECH",
    "LAB_MANAGER",
    "LAB_TECH",
    "AUDITOR",
]


def _validate_password(value: SecretStr) -> SecretStr:
    password = value.get_secret_value()
    if not any(character.isalpha() for character in password) or not any(
        character.isdigit() for character in password
    ):
        raise ValueError("Password must contain at least one letter and one digit")
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must not exceed 72 UTF-8 bytes")
    return value


class UserCreate(BaseModel):
    email: EmailStr
    full_name: Annotated[str, Field(min_length=1, max_length=150)]
    password: Annotated[SecretStr, Field(min_length=10)]
    role: RoleName
    department_id: UUID | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().casefold()

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Full name cannot be blank")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: SecretStr) -> SecretStr:
        return _validate_password(value)

    @model_validator(mode="after")
    def validate_department_scope(self) -> "UserCreate":
        if self.role in {"LAB_MANAGER", "LAB_TECH"} and self.department_id is None:
            raise ValueError(f"{self.role} accounts require a department assignment")
        return self


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: Annotated[str, Field(min_length=1, max_length=150)] | None = None
    role: RoleName | None = None
    department_id: UUID | None = None
    is_active: bool | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr | None) -> str | None:
        return str(value).strip().casefold() if value is not None else None

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("Full name cannot be blank")
        return normalized

    @model_validator(mode="after")
    def require_mutation(self) -> "UserUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        for field in ("email", "full_name", "role", "is_active"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    role: RoleName
    department_id: UUID | None
    is_active: bool
    created_at: datetime


class UserPage(BaseModel):
    items: list[UserRead]
    total: int
    page: int
    size: int
    pages: int


class DepartmentOption(BaseModel):
    id: UUID
    name: str
    code: str
