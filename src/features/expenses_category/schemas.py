from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, field_validator

from src.features.config import DBModel


class ExpCategoryStatus(StrEnum):
    ACTIVE = "ACTIVE"
    IN_ACTIVE = "IN_ACTIVE"


class CreateExpCategory(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_to_lowercase(cls, v: str) -> str:
        return v.lower().strip()


class UpdateExpCategory(BaseModel):
    name: Optional[str] = None
    status: Optional[ExpCategoryStatus] = None

    @field_validator("name")
    @classmethod
    def name_to_lowercase(cls, v: str) -> str:
        return v.lower().strip()


class ExpCategoryResponseModel(DBModel):
    id: int
    name: str
    status: ExpCategoryStatus
