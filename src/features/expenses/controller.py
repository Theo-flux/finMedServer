import uuid
from datetime import datetime
from typing import Optional

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload
from sqlmodel import delete, func, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.expenses import Expenses
from src.features.budgets.controller import BudgetController
from src.features.expenses.schemas import (
    CreateExpensesModel,
    EditExpenseModel,
    ExpensesResponseModel,
    SingleExpenseResponseModel,
)
from src.features.expenses_category.controller import ExpCategoryController
from src.misc.schemas import PaginatedResponseModel, PaginationModel, ServerRespModel
from src.utils import build_serial_no, get_current_and_total_pages
from src.utils.exceptions import InsufficientPermissions, InvalidToken, NotFound

budget_controller = BudgetController()
category_controller = ExpCategoryController()


class ExpensesController:
    async def generate_exp_serial_no(self, exp_uid: uuid.UUID, session: AsyncSession):
        exp = await self.get_exp_by_uid(exp_uid, session)
        serial_no = build_serial_no("Expenses", exp.id)
        statement = update(Expenses).where(Expenses.uid == exp_uid).values(serial_no=serial_no)

        await session.exec(statement)

    async def get_exp_by_uid(self, exp_uid: uuid.UUID, session: AsyncSession):
        statement = (
            select(Expenses)
            .options(
                selectinload(Expenses.user),
                selectinload(Expenses.expenses_category),
                selectinload(Expenses.budget),
            )
            .where(Expenses.uid == exp_uid)
        )
        result = await session.exec(statement)
        exp = result.first()

        return exp

    async def single_exp(self, exp_uid: uuid.UUID, session: AsyncSession):
        exp = await self.get_exp_by_uid(exp_uid=exp_uid, session=session)

        if exp is None:
            raise NotFound("Expenses not found")

        exp_response = SingleExpenseResponseModel.model_validate(exp)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[SingleExpenseResponseModel](
                data=exp_response, message="Expense retrieved!"
            ).model_dump(),
        )

    async def create_exp(self, token_payload: dict, data: CreateExpensesModel, session: AsyncSession):
        exp = data.model_dump()

        budget = await budget_controller.get_budget_by_uid(budget_uid=data.budget_uid, session=session)

        if budget is None:
            raise NotFound("Budget not found!")

        exp_cat = await category_controller.get_category_by_uid(
            category_uid=data.expenses_category_uid, session=session
        )

        if exp_cat is None:
            raise NotFound("Category not found!")

        exp["user_uid"] = token_payload["user"]["uid"]

        try:
            new_exp = Expenses(**exp)

            session.add(new_exp)
            await session.flush()
            await self.generate_exp_serial_no(new_exp.uid, session)
            await session.commit()

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=ServerRespModel[bool](data=True, message="Expense created!").model_dump(),
            )

        except Exception as e:
            await session.rollback()
            raise e

    async def update_exp(self, exp_uid: uuid.UUID, token_payload: dict, data: EditExpenseModel, session: AsyncSession):
        exp_to_update = await self.get_exp_by_uid(exp_uid, session)

        if exp_to_update is None:
            raise NotFound("Expense doesn't exist")

        if str(exp_to_update.user_uid) != token_payload["user"]["uid"]:
            raise InsufficientPermissions("You don't have the permission to update this expense!")

        valid_attrs = data.model_dump(exclude_none=True)
        if valid_attrs:
            valid_attrs["updated_at"] = datetime.now()
            statement = update(Expenses).where(Expenses.uid == exp_uid).values(**valid_attrs)
            await session.exec(statement=statement)
            await session.commit()
            await session.refresh(exp_to_update)

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=ServerRespModel[bool](data=True, message="Expense updated!").model_dump(),
        )

    async def get_expenses(
        self,
        limit: int,
        token_payload: dict,
        session: AsyncSession,
        offset: int,
        budget_uid: Optional[uuid.UUID] = None,
        q: Optional[str] = None,
    ):
        user_uid = token_payload["user"]["uid"]
        if not user_uid:
            raise InvalidToken()

        query = (
            select(Expenses)
            .options(selectinload(Expenses.budget), selectinload(Expenses.expenses_category))
            .where(Expenses.user_uid == user_uid)
        )

        if budget_uid:
            query = query.where(Expenses.budget_uid == budget_uid)

        if q:
            search_term = f"%{q}%"
            query = query.where(
                Expenses.title.ilike(search_term)
                | Expenses.short_description.ilike(search_term)
                | Expenses.serial_no.ilike(search_term)
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query)

        query = query.order_by(Expenses.created_at.desc()).offset(offset).limit(limit)

        results = await session.exec(query)
        exps = results.all()
        exps_response = [ExpensesResponseModel.model_validate(exp) for exp in exps]
        current_page, total_pages = get_current_and_total_pages(
            limit=limit,
            total=total,
            offset=offset,
        )
        paginated_exp = PaginatedResponseModel.model_validate(
            {
                "items": exps_response,
                "pagination": PaginationModel(
                    total=total, current_page=current_page, limit=limit, total_pages=total_pages
                ),
            }
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[PaginatedResponseModel[ExpensesResponseModel]](
                data=paginated_exp, message="Expenses retrieved successfully"
            ).model_dump(),
        )

    async def delete_exp(
        self,
        exp_uid: uuid.UUID,
        token_payload: dict,
        session: AsyncSession,
    ):
        user_uid = token_payload["user"]["uid"]
        if not user_uid:
            raise InvalidToken()

        exp_exists = await session.exec(select(Expenses).where(Expenses.user_uid == user_uid, Expenses.uid == exp_uid))

        if not exp_exists.first():
            raise NotFound("Expense not found!")

        statement = delete(Expenses).where(Expenses.user_uid == user_uid, Expenses.uid == exp_uid)
        await session.exec(statement)
        await session.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[bool](data=True, message="Expense deleted successfully!").model_dump(),
        )
