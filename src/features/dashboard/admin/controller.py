from typing import List

from sqlalchemy import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.budgets import Budget
from src.db.models.departments import Department
from src.db.models.expenses import Expenses
from src.features.dashboard.admin.schema import BudgetUtilizationModel, PeriodicAnalyticsParams
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AdminController:
    async def budget_utilization_by_department(
        self, params: PeriodicAnalyticsParams, session: AsyncSession
    ) -> List[BudgetUtilizationModel]:
        """Calculate budget utilization per department within date range"""
        try:
            start_date, end_date = params.get_date_range()
            logger.info(f"Calculating budget utilization from {start_date} to {end_date}")

            statement = (
                select(
                    Department.name.label("department_name"),
                    Budget.department_uid,
                    func.sum(Budget.gross_amount).label("total_budget"),
                    func.coalesce(func.sum(Expenses.amount_spent), 0).label("total_expenses"),
                )
                .join(Department, Department.uid == Budget.department_uid)
                .outerjoin(Expenses, Budget.uid == Expenses.budget_uid)
                .where(Budget.created_at >= start_date, Budget.created_at <= end_date)
                .group_by(Department.name, Budget.department_uid)
                .order_by(Department.name)
            )

            result = await session.exec(statement=statement)
            utilization_data = []

            for row in result:
                total_budget = float(row.total_budget or 0)
                total_expenses = float(row.total_expenses or 0)
                utilization_percentage = (total_expenses / total_budget * 100) if total_budget > 0 else 0
                utilization = BudgetUtilizationModel.model_validate(
                    {
                        "department_name": row.department_name,
                        "department_uid": row.department_uid,
                        "total_budget": total_budget,
                        "total_expenses": total_expenses,
                        "utilization_percentage": round(utilization_percentage, 2),
                        "remaining_budget": total_budget - total_expenses,
                    }
                )
                utilization_data.append(utilization)

            logger.info(f"Successfully calculated utilization for {len(utilization_data)} departments")
            return utilization_data

        except Exception as e:
            logger.error(f"Error calculating budget utilization: {e}")
            raise


admin_controller = AdminController()
