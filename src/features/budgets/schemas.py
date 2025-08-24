import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field, field_serializer

from src.features.config import DBModel
from src.features.departments.schemas import DeptResponseModel


class BudgetStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class BudgetAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    FROZEN = "FROZEN"
    DEPLETED = "DEPLETED"
    RESERVED = "RESERVED"


class CreateBudgetModel(BaseModel):
    gross_amount: int = Field(ge=1000)
    title: str
    short_description: str
    department_uid: uuid.UUID


class EditBudgetModel(BaseModel):
    gross_amount: Optional[int] = None
    title: Optional[str] = None
    short_description: Optional[str] = None
    department_uid: Optional[uuid.UUID] = None
    assignee_uid: Optional[uuid.UUID] = None


class BudgetUserResponseModel(DBModel):
    uid: uuid.UUID
    first_name: str
    last_name: str
    email: str
    staff_no: str


class BudgetResponseModel(DBModel):
    id: int
    serial_no: str
    received_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    department_uid: uuid.UUID
    user_uid: uuid.UUID
    approver_uid: Optional[uuid.UUID] = None
    assignee_uid: Optional[uuid.UUID] = None
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
    def serialize_buuid(self, value: uuid.UUID, _info):
        if value:
            return str(value)

    @field_serializer("gross_amount", "amount_remaining")
    def serialize_decimal(self, value: Decimal, _info):
        return float(value)


class SingleBudgetResponseModel(BudgetResponseModel):
    department: DeptResponseModel
    user: BudgetUserResponseModel
    approver: Optional[BudgetUserResponseModel] = None
    assignee: Optional[BudgetUserResponseModel] = None
