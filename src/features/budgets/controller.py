from sqlmodel.ext.asyncio.session import AsyncSession

from src.features.budgets.schemas import CreateBudget


class BudgetControllers:
    async def create_budget(data: CreateBudget, session: AsyncSession):
        pass
