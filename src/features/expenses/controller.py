import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from src.features.expenses.schemas import CreateExpensesModel


class ExpensesController:
    async def get_exp_by_uid(self, expenses_uid: uuid.UUID, session: AsyncSession):
        pass

    async def create_exp(self, budget_uid: uuid.UUID, data: CreateExpensesModel, session: AsyncSession):
        pass
