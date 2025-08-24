import uuid
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_serializer

from src.features.budgets.schemas import BudgetResponseModel, BudgetUserResponseModel
from src.features.config import DBModel
from src.features.expenses_category.schemas import ExpCategoryResponseModel


class EditExpenseModel(BaseModel):
    amount_spent: Optional[int] = Field(gt=0, default=None)
    title: Optional[str] = None
    short_description: Optional[str] = None
    budget_uid: Optional[uuid.UUID] = None
    expenses_category_uid: Optional[uuid.UUID] = None


class CreateExpensesModel(BaseModel):
    amount_spent: int = Field(gt=0)
    title: str
    short_description: str
    note: Optional[str] = Field(default="")
    budget_uid: uuid.UUID
    expenses_category_uid: uuid.UUID


class ExpensesResponseModel(DBModel):
    id: int
    serial_no: str
    budget_uid: uuid.UUID
    expenses_category_uid: uuid.UUID
    user_uid: uuid.UUID
    amount_spent: Decimal
    title: str
    short_description: str
    note: str
    expenses_category: ExpCategoryResponseModel
    budget: BudgetResponseModel

    @field_serializer("budget_uid", "expenses_category_uid", "user_uid")
    def serialize_buuid(self, value: uuid.UUID, _info):
        if value:
            return str(value)

    @field_serializer("amount_spent")
    def serialize_decimal(self, value: Decimal, _info):
        return float(value)


class SingleExpenseResponseModel(ExpensesResponseModel):
    user: BudgetUserResponseModel
