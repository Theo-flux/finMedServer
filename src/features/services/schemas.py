from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, field_validator

from src.features.config import DBModel


class ServiceStatus(StrEnum):
    ACTIVE = "ACTIVE"
    IN_ACTIVE = "IN_ACTIVE"


class CreateServiceModel(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_to_lowercase(cls, v: str) -> str:
        return v.lower().strip()


class UpdateServiceModel(BaseModel):
    name: Optional[str] = None
    status: Optional[ServiceStatus] = None

    @field_validator("name")
    @classmethod
    def name_to_lowercase(cls, v: str) -> str:
        return v.lower().strip()


class ServiceResponseModel(DBModel):
    id: int
    name: str
    status: ServiceStatus
