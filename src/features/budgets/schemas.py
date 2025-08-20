import uuid
from enum import StrEnum

from pydantic import BaseModel


class BudgetStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class BudgetAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    FROZEN = "FROZEN"
    DEPLETED = "DEPLETED"
    RESERVED = "RESERVED"


class CreateBudget(BaseModel):
    gross_amount: int
    title: str
    short_description: str
    department_uid: uuid.UUID
