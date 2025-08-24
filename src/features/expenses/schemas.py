import uuid
from typing import Optional

from pydantic import BaseModel, Field


class CreateExpensesModel(BaseModel):
    amount_spent: int
    title: str
    short_description: str
    note: Optional[str] = Field(default="")
    expenses_category_uid: uuid.UUID
