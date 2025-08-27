from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload
from sqlmodel import delete, func, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.budgets import Budget
from src.features.budgets.schemas import (
    BudgetResponseModel,
    CreateBudgetModel,
    EditBudgetModel,
    SingleBudgetResponseModel,
)
from src.features.config import SelectOfScalar
from src.features.roles.controller import RoleController
from src.misc.schemas import PaginatedResponseModel, PaginationModel, ServerRespModel
from src.utils import build_serial_no, get_current_and_total_pages
from src.utils.exceptions import InsufficientPermissions, InvalidToken, NotFound

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

    async def update_budget(self, budget_uid: UUID, token_payload: dict, data: EditBudgetModel, session: AsyncSession):
        budget_to_update = await self.get_budget_by_uid(budget_uid, session)

        if budget_to_update is None:
            raise NotFound("Budget doesn't exist")

        if str(budget_to_update.user_uid) != token_payload["user"]["uid"]:
            raise InsufficientPermissions("You don't have the permission to update this budget!")

        valid_attrs = data.model_dump(exclude_none=True)
        if valid_attrs:
            valid_attrs["updated_at"] = datetime.now()
            statement = update(Budget).where(Budget.uid == budget_uid).values(**valid_attrs)
            await session.exec(statement=statement)
            await session.commit()
            await session.refresh(budget_to_update)

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=ServerRespModel[bool](data=True, message="Budget updated!").model_dump(),
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
        budgets_response = [BudgetResponseModel.model_validate(budget) for budget in budgets]
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
            content=ServerRespModel[PaginatedResponseModel[BudgetResponseModel]](
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

        if not user_uid or not role_uid:
            raise InvalidToken()

        query = select(Budget)

        if not await role_controller.is_role_admin(role_uid=role_uid, session=session):
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

        query = select(Budget)

        if not await role_controller.is_role_admin(role_uid=role_uid, session=session):
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
