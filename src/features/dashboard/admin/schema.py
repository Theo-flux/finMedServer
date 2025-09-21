from calendar import monthrange
from datetime import date
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class MonthRange(str, Enum):
    ONE_MONTH = "1"
    THREE_MONTHS = "3"
    SIX_MONTHS = "6"
    TWELVE_MONTHS = "12"


class PeriodicAnalyticsParams(BaseModel):
    month_range: MonthRange = Field(default=MonthRange.ONE_MONTH, description="Number of months to analyze")
    end_month: Optional[int] = Field(
        default=date.today().month, ge=1, le=12, description="End month (1-12). Defaults to current month"
    )
    end_year: Optional[int] = Field(default=date.today().year, description="End year. Defaults to current year")

    @field_validator("end_year", "end_month", mode="before")
    def set_default_dates(cls, value, field):
        if value is None:
            today = date.today()
            if field.name == "end_month":
                return today.month
            if field.name == "end_year":
                return today.year
        return value

    def get_date_range(self) -> tuple[date, date]:
        """Calculate start and end dates based on month range"""
        end_date = date(
            year=self.end_year,
            month=self.end_month,
            day=monthrange(self.end_year, self.end_month)[1],
        )

        months_back = int(self.month_range)
        start_year = self.end_year
        start_month = self.end_month - months_back

        while start_month <= 0:
            start_month += 12
            start_year -= 1

        start_date = date(year=start_year, month=start_month, day=1)

        return start_date, end_date


class BudgetUtilizationModel(BaseModel):
    department_name: str
    department_uid: UUID
    total_budget: float
    total_expenses: float
    utilization_percentage: float
    remaining_budget: float

    @field_serializer("department_uid")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)

    model_config = ConfigDict(from_attributes=True)


class IncomeModel(BaseModel):
    department_name: str
    department_uid: UUID
    total_budget: float
    total_expenses: float
    utilization_percentage: float
    remaining_budget: float

    @field_serializer("department_uid")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)

    model_config = ConfigDict(from_attributes=True)
