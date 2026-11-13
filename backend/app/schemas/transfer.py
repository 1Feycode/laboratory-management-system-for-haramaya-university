from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

TransferStatus = Literal[
    "PENDING_RECEIVER",
    "PENDING_ULMD",
    "COMPLETED",
    "REJECTED",
]


class TransferCreate(BaseModel):
    asset_id: UUID
    target_laboratory_id: UUID
    target_room_id: UUID
    transfer_reason: Annotated[str, Field(min_length=1, max_length=4000)]

    @model_validator(mode="before")
    @classmethod
    def trim_text_fields(cls, value):
        if isinstance(value, dict):
            return {
                key: item.strip() if isinstance(item, str) else item
                for key, item in value.items()
            }
        return value


class TransferAcceptance(BaseModel):
    notes: Annotated[str, Field(max_length=4000)] | None = None

    @model_validator(mode="before")
    @classmethod
    def trim_text_fields(cls, value):
        if isinstance(value, dict):
            return {
                key: item.strip() if isinstance(item, str) else item
                for key, item in value.items()
            }
        return value


class TransferRejection(BaseModel):
    notes: Annotated[str, Field(min_length=1, max_length=4000)]

    @model_validator(mode="before")
    @classmethod
    def trim_text_fields(cls, value):
        if isinstance(value, dict):
            return {
                key: item.strip() if isinstance(item, str) else item
                for key, item in value.items()
            }
        return value


class TransferStatusEvent(BaseModel):
    action: str
    actor_id: UUID | None
    actor_name: str | None
    old_status: TransferStatus | None
    new_status: TransferStatus
    notes: str | None
    occurred_at: datetime


class TransferRead(BaseModel):
    id: UUID
    asset_id: UUID
    asset_code: str
    origin_laboratory_id: UUID
    origin_laboratory_name: str
    origin_room_id: UUID
    origin_room_number: str
    origin_building_name: str
    target_laboratory_id: UUID
    target_laboratory_name: str
    target_room_id: UUID
    target_room_number: str
    target_building_name: str
    initiated_by: UUID
    initiator_name: str
    accepted_by: UUID | None
    accepter_name: str | None
    approved_by_ulmd: UUID | None
    approver_name: str | None
    status: TransferStatus
    transfer_reason: str
    notes: str | None
    created_at: datetime
    completed_at: datetime | None
    status_history: list[TransferStatusEvent] = Field(default_factory=list)


class TransferPage(BaseModel):
    items: list[TransferRead]
    total: int
    page: int
    size: int
    pages: int
