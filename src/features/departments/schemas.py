from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, field_validator

from src.features.config import DBModel


class DepartmentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    IN_ACTIVE = "IN_ACTIVE"


class CreateDept(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_to_lowercase(cls, v: str) -> str:
        return v.lower().strip()


class UpdateDept(BaseModel):
    name: Optional[str] = None
    status: Optional[DepartmentStatus] = None

    @field_validator("name")
    @classmethod
    def name_to_lowercase(cls, v: str) -> str:
        return v.lower().strip()


class DeptResponse(DBModel):
    id: int
    name: str
    status: DepartmentStatus
