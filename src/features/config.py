from datetime import datetime
from enum import StrEnum
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from sqlalchemy.sql.selectable import Select

T = TypeVar("T")
SelectOfScalar = Select[T]


class Gender(StrEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class DBModel(BaseModel):
    uid: UUID
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_dt(self, value: datetime, _info):
        return value.isoformat()

    @field_serializer("uid")
    def serialize_uuid(self, value: UUID, _info):
        return str(value)

    model_config = ConfigDict(from_attributes=True)


class EmailOrStaffNoModel(BaseModel):
    email_or_staff_no: str = Field(...)

    @field_validator("email_or_staff_no")
    @classmethod
    def validate_email_or_staff_no(cls, value: str):
        if not value.strip():
            raise ValueError("Email or Staff Number cannot be empty")
        return value

    model_config = ConfigDict(from_attributes=True)


class AbridgedUserResponseModel(DBModel):
    id: int
    first_name: str
    last_name: str
    email: str
    staff_no: str
