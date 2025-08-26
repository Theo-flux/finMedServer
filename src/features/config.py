import uuid
from datetime import datetime
from enum import StrEnum
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, field_serializer
from sqlalchemy.sql.selectable import Select

T = TypeVar("T")
SelectOfScalar = Select[T]


class Gender(StrEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class DBModel(BaseModel):
    uid: uuid.UUID
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_dt(self, value: datetime, _info):
        return value.isoformat()

    @field_serializer("uid")
    def serialize_uuid(self, value: uuid.UUID, _info):
        return str(value)

    model_config = ConfigDict(from_attributes=True)


class AbridgedUserResponseModel(DBModel):
    id: int
    first_name: str
    last_name: str
    email: str
    staff_no: str
