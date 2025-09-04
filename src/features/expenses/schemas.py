from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from src.features.budgets.schemas import BudgetResponseModel
from src.features.config import AbridgedUserResponseModel, DBModel
from src.features.expenses_category.schemas import ExpCategoryResponseModel


class EditExpenseModel(BaseModel):
    amount_spent: Optional[int] = Field(gt=0, default=None)
    title: Optional[str] = None
    short_description: Optional[str] = None
    budget_uid: Optional[UUID] = None
    expenses_category_uid: Optional[UUID] = None


class CreateExpensesModel(BaseModel):
    amount_spent: int = Field(gt=0)
    title: str
    short_description: str
    note: Optional[str] = Field(default="")
    budget_uid: UUID
    expenses_category_uid: UUID


class ExpensesResponseModel(DBModel):
    id: int
    serial_no: str
    budget_uid: UUID
    expenses_category_uid: UUID
    user_uid: UUID
    amount_spent: Decimal
    title: str
    short_description: str
    note: str
    expenses_category: ExpCategoryResponseModel

    @field_serializer("budget_uid", "expenses_category_uid", "user_uid")
    def serialize_buuid(self, value: UUID, _info):
        if value:
            return str(value)

    @field_serializer("amount_spent")
    def serialize_decimal(self, value: Decimal, _info):
        return float(value)


class SingleExpenseResponseModel(ExpensesResponseModel):
    user: AbridgedUserResponseModel
    expenses_category: ExpCategoryResponseModel
    budget: BudgetResponseModel
