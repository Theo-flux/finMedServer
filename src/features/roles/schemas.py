import uuid
from datetime import datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RoleStatus(StrEnum):
    ACTIVE = "ACTIVE"
    IN_ACTIVE = "IN_ACTIVE"


class UserRoles(BaseModel):
    id: int
    uid: uuid.UUID
    created_at: datetime
    updated_at: datetime
    name: str
    status: RoleStatus


class CreateRole(BaseModel):
    name: str


class UpdateRole(BaseModel):
    name: Optional[str] = None
    status: Optional[RoleStatus] = None


class RoleResponse(BaseModel):
    uid: uuid.UUID
    name: str
    status: RoleStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
