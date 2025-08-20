from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, field_validator

from src.features.config import DBModel


class RoleStatus(StrEnum):
    ACTIVE = "ACTIVE"
    IN_ACTIVE = "IN_ACTIVE"


class CreateRole(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_to_lowercase(cls, v: str) -> str:
        return v.lower().strip()


class UpdateRole(BaseModel):
    name: Optional[str] = None
    status: Optional[RoleStatus] = None

    @field_validator("name")
    @classmethod
    def name_to_lowercase(cls, v: str) -> str:
        return v.lower().strip()


class RoleResponseModel(DBModel):
    id: int
    name: str
    status: RoleStatus
