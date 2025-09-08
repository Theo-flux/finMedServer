from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload
from sqlmodel import delete, func, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.budgets import Budget
from src.db.models.expenses import Expenses
from src.features.budgets.schemas import BudgetStatus, CreateBudgetModel, SingleBudgetResponseModel, UpdateBudgetModel
from src.features.config import SelectOfScalar
from src.features.expenses.schemas import SingleExpenseResponseModel
from src.features.roles.controller import RoleController
from src.misc.schemas import PaginatedResponseModel, PaginationModel, ServerRespModel
from src.utils import build_serial_no, get_current_and_total_pages
from src.utils.exceptions import BadRequest, InsufficientPermissions, InvalidToken, NotFound

role_controller = RoleController()


class BudgetController:
    async def generate_budget_serial_no(self, budget_uid: UUID, session: AsyncSession):
        budget = await self.get_budget_by_uid(budget_uid, session)
        serial_no = build_serial_no("Budget", budget.id)
        statement = update(Budget).where(Budget.uid == budget_uid).values(serial_no=serial_no)

        await session.exec(statement)

    async def get_budget_by_uid(self, budget_uid: UUID, session: AsyncSession):
        statement = (
            select(Budget)
            .options(
                selectinload(Budget.department),
                selectinload(Budget.user),
                selectinload(Budget.approver),
                selectinload(Budget.assignee),
            )
            .where(Budget.uid == budget_uid)
        )
        result = await session.exec(statement)
        budget = result.first()

        return budget

    async def get_budget_with_expenses(self, budget_uid: UUID, session: AsyncSession):
        statement = select(Budget).options(selectinload(Budget.expenses)).where(Budget.uid == budget_uid)
        result = await session.exec(statement=statement)

        return result.first()

    async def single_budget(self, budget_uid: UUID, session: AsyncSession):
        budget = await self.get_budget_by_uid(budget_uid=budget_uid, session=session)

        if budget is None:
            raise NotFound("Budget not found")

        budget_response = SingleBudgetResponseModel.model_validate(budget)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[SingleBudgetResponseModel](
                data=budget_response, message="Budget retrieved!"
            ).model_dump(),
        )

    async def create_budget(self, token_payload: dict, data: CreateBudgetModel, session: AsyncSession):
        budget = data.model_dump()
        if await role_controller.is_role_admin(role_uid=token_payload["user"]["role_uid"], session=session):
            budget["status"] = BudgetStatus.APPROVED.value
            budget["approved_at"] = datetime.now(timezone.utc)

        budget["user_uid"] = token_payload["user"]["uid"]

        try:
            new_budget = Budget(**budget)

            session.add(new_budget)
            await session.flush()
            await self.generate_budget_serial_no(new_budget.uid, session)
            await session.commit()

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=ServerRespModel[bool](data=True, message="Budget created!").model_dump(),
            )

        except Exception as e:
            await session.rollback()
            raise e

    async def update_budget(
        self, budget_uid: UUID, token_payload: dict, data: UpdateBudgetModel, session: AsyncSession
    ):
        budget_to_update = await self.get_budget_with_expenses(budget_uid, session)

        if budget_to_update is None:
            raise NotFound("Budget doesn't exist")

        if str(budget_to_update.user_uid) != token_payload["user"]["uid"]:
            raise InsufficientPermissions("You don't have the permission to update this budget!")

        valid_attrs = data.model_dump(exclude_none=True)
        if not valid_attrs:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=ServerRespModel[bool](data=True, message="No changes to update").model_dump(),
            )

        financial_fields = {"gross_amount"}
        valid_attrs["updated_at"] = datetime.now(timezone.utc)

        if any(field in valid_attrs for field in financial_fields):
            new_gross_amount = valid_attrs.get("gross_amount")

            if new_gross_amount and new_gross_amount < budget_to_update.total_expenses:
                raise BadRequest("New budget amount cannot be lower than existing expenses!")

        for field, value in valid_attrs.items():
            setattr(budget_to_update, field, value)

        try:
            statement = update(Budget).where(Budget.uid == budget_uid).values(**valid_attrs)
            await session.exec(statement=statement)
            await session.commit()
            await session.refresh(budget_to_update)
        except Exception as e:
            await session.rollback()
            raise BadRequest(f"Failed to update budget: {str(e)}")

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=ServerRespModel[bool](data=True, message="Budget updated successfully!").model_dump(),
        )

    async def get_budgets(
        self,
        limit: int,
        query: SelectOfScalar[Budget],
        session: AsyncSession,
        budget_status: Optional[str],
        budget_availability: Optional[str],
        q: Optional[str] = None,
        offset: Optional[int] = None,
    ):

        if q:
            search_term = f"%{q}%"
            query = query.where(
                Budget.title.ilike(search_term)
                | Budget.short_description.ilike(search_term)
                | Budget.serial_no.ilike(search_term)
            )

        if budget_status:
            query = query.where(Budget.status == budget_status)

        if budget_availability:
            query = query.where(Budget.availability == budget_availability)

        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query)

        query = query.order_by(Budget.created_at.desc()).offset(offset).limit(limit)

        results = await session.exec(query)
        budgets = results.all()
        budgets_response = [SingleBudgetResponseModel.model_validate(budget) for budget in budgets]
        current_page, total_pages = get_current_and_total_pages(
            limit=limit,
            total=total,
            offset=offset,
        )
        paginated_budget = PaginatedResponseModel.model_validate(
            {
                "items": budgets_response,
                "pagination": PaginationModel(
                    total=total, current_page=current_page, limit=limit, total_pages=total_pages
                ),
            }
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[PaginatedResponseModel[SingleBudgetResponseModel]](
                data=paginated_budget, message="Budgets retrieved successfully"
            ).model_dump(),
        )

    async def get_user_budget(
        self,
        limit: int,
        token_payload: dict,
        session: AsyncSession,
        budget_status: Optional[str],
        budget_availability: Optional[str],
        q: Optional[str] = None,
        offset: Optional[int] = None,
    ):
        user_uid = token_payload["user"]["uid"]
        role_uid = token_payload["user"]["role_uid"]
        department_uid = token_payload["user"]["department_uid"]

        if not user_uid or not role_uid:
            raise InvalidToken()

        query = select(Budget).options(
            selectinload(Budget.department),
            selectinload(Budget.user),
            selectinload(Budget.approver),
            selectinload(Budget.assignee),
        )

        if not await role_controller.is_role_admin(role_uid=role_uid, session=session):
            role = await role_controller.get_role_by_uid(role_uid=role_uid, session=session)

            if role and role.name == "subadmin":
                query = query.where(Budget.department_uid == department_uid)
            else:
                query = query.where(Budget.user_uid == user_uid)

        return await self.get_budgets(
            q=q,
            limit=limit,
            offset=offset,
            query=query,
            session=session,
            budget_availability=budget_availability,
            budget_status=budget_status,
        )

    async def get_assigned_budget(
        self,
        limit: int,
        token_payload: dict,
        session: AsyncSession,
        budget_status: Optional[str],
        budget_availability: Optional[str],
        q: Optional[str] = None,
        offset: Optional[int] = None,
    ):
        user_uid = token_payload["user"]["uid"]
        role_uid = token_payload["user"]["role_uid"]

        if not user_uid or not role_uid:
            raise InvalidToken()

        query = select(Budget).options(
            selectinload(Budget.department),
            selectinload(Budget.user),
            selectinload(Budget.approver),
            selectinload(Budget.assignee),
        )

        query = query.where(Budget.assignee_uid == user_uid)

        return await self.get_budgets(
            q=q,
            limit=limit,
            offset=offset,
            query=query,
            session=session,
            budget_availability=budget_availability,
            budget_status=budget_status,
        )

    async def get_budget_expenses(
        self,
        budget_uid: UUID,
        q: Optional[str],
        limit: int,
        offset: int,
        expenses_category_uid: Optional[UUID],
        token_payload: dict,
        session: AsyncSession,
    ):
        user_uid = token_payload["user"]["uid"]
        if not user_uid:
            raise InvalidToken()

        query = (
            select(Expenses)
            .options(
                selectinload(Expenses.budget), selectinload(Expenses.expenses_category), selectinload(Expenses.user)
            )
            .where(Expenses.budget_uid == budget_uid)
        )

        if q:
            query = query.where(
                Expenses.title.ilike(f"%{q}")
                | Expenses.serial_no.ilike(f"%{q}")
                | Expenses.note.ilike(f"%{q}")
                | Expenses.short_description.ilike(f"%{q}")
            )

        if expenses_category_uid:
            query = query.where(Expenses.expenses_category_uid == expenses_category_uid)

        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query)

        query = query.order_by(Expenses.created_at.desc()).offset(offset).limit(limit)
        results = await session.exec(query)
        budget_expenses = results.all()
        budget_expenses_response = [SingleExpenseResponseModel.model_validate(expense) for expense in budget_expenses]
        current_page, total_pages = get_current_and_total_pages(
            limit=limit,
            total=total,
            offset=offset,
        )

        paginated_invoice_payments = PaginatedResponseModel.model_validate(
            {
                "items": budget_expenses_response,
                "pagination": PaginationModel(
                    total=total, current_page=current_page, limit=limit, total_pages=total_pages
                ),
            }
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[PaginatedResponseModel[SingleExpenseResponseModel]](
                data=paginated_invoice_payments, message="Budget Expenses retrieved successfully"
            ).model_dump(),
        )

    async def delete_budget(
        self,
        budget_uid: UUID,
        token_payload: dict,
        session: AsyncSession,
    ):
        user_uid = token_payload["user"]["uid"]
        if not user_uid:
            raise InvalidToken()

        budget_exists = await session.exec(select(Budget).where(Budget.user_uid == user_uid, Budget.uid == budget_uid))

        if not budget_exists.first():
            raise NotFound("Budget not found!")

        statement = delete(Budget).where(Budget.user_uid == user_uid, Budget.uid == budget_uid)
        await session.exec(statement)
        await session.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[bool](data=True, message="Budget deleted successfully!").model_dump(),
        )

    async def update_availability(self, budget_uid: UUID, availability: BudgetStatus, session: AsyncSession):
        budget = await self.get_budget_by_uid(budget_uid, session)

        if not budget:
            raise NotFound("Budget not found!")

        if budget.availability == availability.value:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=ServerRespModel[bool](data=True, message="Budget updated successfully!").model_dump(),
            )

        try:
            statement = update(Budget).where(Budget.uid == budget_uid).values(availability=availability.value)
            await session.exec(statement=statement)
            await session.commit()

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=ServerRespModel[bool](data=True, message="Budget updated successfully!").model_dump(),
            )
        except Exception:
            await session.rollback()
            raise BadRequest("Failed to update budget availability")

    async def update_status(self, budget_uid: UUID, budget_status: BudgetStatus, session: AsyncSession):
        budget = await self.get_budget_by_uid(budget_uid, session)

        if not budget:
            raise NotFound("Budget not found!")

        if budget.status == budget_status.value:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=ServerRespModel[bool](data=True, message="Budget updated successfully!").model_dump(),
            )

        try:
            statement = update(Budget).where(Budget.uid == budget_uid).values(status=budget_status.value)
            await session.exec(statement=statement)
            await session.commit()

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=ServerRespModel[bool](data=True, message="Budget updated successfully!").model_dump(),
            )
        except Exception:
            await session.rollback()
            raise BadRequest("Failed to update budget status")
