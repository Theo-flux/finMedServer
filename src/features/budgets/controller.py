import uuid
from datetime import datetime
from typing import Optional

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload
from sqlmodel import select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.budgets import Budget
from src.features.budgets.schemas import BudgetResponseModel, CreateBudgetModel, EditBudgetModel
from src.features.roles.controller import RoleController
from src.misc.schemas import ServerRespModel
from src.utils import build_serial_no
from src.utils.exceptions import InsufficientPermissions, NotFound

role_controller = RoleController()


class BudgetControllers:
    async def generate_budget_serial_no(self, budget_uid: uuid.UUID, session: AsyncSession):
        budget = await self.get_budget_by_uid(budget_uid, session)
        serial_no = build_serial_no("Budget", budget.id)
        statement = update(Budget).where(Budget.uid == budget_uid).values(serial_no=serial_no)

        await session.exec(statement)

    async def get_budget_by_uid(self, budget_uid: uuid.UUID, session: AsyncSession):
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

    async def single_budget(self, budget_uid: uuid.UUID, session: AsyncSession):
        budget = await self.get_budget_by_uid(budget_uid=budget_uid, session=session)

        if budget is None:
            raise NotFound("Budget not found")

        budget_response = BudgetResponseModel.model_validate(budget)
        print(budget_response.model_dump_json())

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[BudgetResponseModel](
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

        except Exception as e:
            await session.rollback()
            raise e

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=ServerRespModel[bool](data=True, message="Budget created!").model_dump(),
        )

    async def update_budget(
        self, budget_uid: uuid.UUID, token_payload: dict, data: EditBudgetModel, session: AsyncSession
    ):
        budget_to_update = await self.get_budget_by_uid(budget_uid, session)

        if budget_to_update is None:
            raise NotFound("Budget doesn't exist")

        if budget_to_update.user_uid is not token_payload["user"]["uid"]:
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

    async def get_my_budget(
        self,
        limit: int,
        token_payload: dict,
        session: AsyncSession,
        next_cursor: Optional[int] = None,
    ):
        pass

    async def get_assigned_budget(
        self,
        limit: int,
        token_payload: dict,
        session: AsyncSession,
        next_cursor: Optional[int] = None,
    ):
        pass
