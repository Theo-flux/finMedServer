from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from src.features.config import AbridgedUserResponseModel, DBModel
from src.features.departments.schemas import DeptResponseModel


class BudgetStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class BudgetAssignModel(BaseModel):
    assignee_uid: UUID


class BudgetAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    FROZEN = "FROZEN"
    DEPLETED = "DEPLETED"
    RESERVED = "RESERVED"


class CreateBudgetModel(BaseModel):
    gross_amount: int = Field(ge=1000)
    title: str
    short_description: str
    department_uid: UUID


class UpdateBudgetModel(BaseModel):
    gross_amount: Optional[int] = None
    title: Optional[str] = None
    short_description: Optional[str] = None
    department_uid: Optional[UUID] = None
    assignee_uid: Optional[UUID] = None
    status: Optional[BudgetStatus] = None
    availability: Optional[BudgetStatus] = None


class BudgetResponseModel(DBModel):
    id: int
    serial_no: str
    received_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    department_uid: UUID
    user_uid: UUID
    approver_uid: Optional[UUID] = None
    assignee_uid: Optional[UUID] = None
    status: str
    availability: str
    gross_amount: Decimal
    amount_remaining: Decimal
    title: str
    short_description: str

    @field_serializer("received_at", "approved_at")
    def serialize_bdt(self, value: datetime, _info):
        if value:
            return value.isoformat()

    @field_serializer("department_uid", "user_uid", "approver_uid", "assignee_uid")
    def serialize_buuid(self, value: UUID, _info):
        if value:
            return str(value)

    @field_serializer("gross_amount", "amount_remaining")
    def serialize_decimal(self, value: Decimal, _info):
        return float(value)


class SingleBudgetResponseModel(BudgetResponseModel):
    department: DeptResponseModel
    user: AbridgedUserResponseModel
    approver: Optional[AbridgedUserResponseModel] = None
    assignee: Optional[AbridgedUserResponseModel] = None
