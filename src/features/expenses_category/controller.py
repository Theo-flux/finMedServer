from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import status
from fastapi.responses import JSONResponse
from sqlmodel import select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.expenses_category import ExpensesCategory
from src.features.expenses_category.schemas import (
    CreateExpCategory,
    ExpCategoryResponseModel,
    ExpCategoryStatus,
    UpdateExpCategory,
)
from src.misc.schemas import ServerRespModel
from src.utils.exceptions import NotFound, ResourceExists


class ExpCategoryController:
    async def get_category_by_uid(self, category_uid: UUID, session: AsyncSession):
        statement = select(ExpensesCategory).where(ExpensesCategory.uid == category_uid)
        result = await session.exec(statement=statement)

        return result.first()

    async def get_category_by_name(self, exp_category_name: str, session: AsyncSession):
        statement = select(ExpensesCategory).where(ExpensesCategory.name == exp_category_name.lower())
        result = await session.exec(statement=statement)

        category = result.first()

        return category

    def is_category_active(self, exp_category: ExpensesCategory):
        return False if exp_category.status == ExpCategoryStatus.IN_ACTIVE.value else True

    async def category_exists(self, category_uid: UUID, session: AsyncSession):
        category = self.get_category_by_uid(category_uid, session)

        if category is None:
            return False

        self.is_category_active(category)

    async def create_category(self, category: CreateExpCategory, session: AsyncSession):
        data = category.model_dump()

        if await self.get_category_by_name(data.get("name"), session):
            raise ResourceExists("Department exists.")

        new_category = ExpensesCategory(**data)

        session.add(new_category)
        await session.commit()

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=ServerRespModel[bool](data=True, message="Expenses Category created!").model_dump(),
        )

    async def update_category(self, category_uid: UUID, data: UpdateExpCategory, session: AsyncSession):
        exp_to_exp = await self.get_category_by_uid(category_uid, session)

        if exp_to_exp is None:
            raise NotFound("Department not found.")

        valid_attrs = data.model_dump(exclude_none=True)

        if valid_attrs:
            valid_attrs["updated_at"] = datetime.now()
            statement = update(ExpensesCategory).where(ExpensesCategory.uid == category_uid).values(**valid_attrs)
            await session.exec(statement=statement)
            await session.commit()
            await session.refresh(exp_to_exp)

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=ServerRespModel[bool](data=True, message="Expenses Category updated!").model_dump(),
        )

    async def get_all_categories(self, session: AsyncSession):
        statement = select(ExpensesCategory)
        result = await session.exec(statement=statement)
        categories = result.all()

        exp_category_responses = [
            ExpCategoryResponseModel.model_validate(category, from_attributes=True) for category in categories
        ]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[List[ExpCategoryResponseModel]](
                data=exp_category_responses, message="Expenses Category retrieved successfully!"
            ).model_dump(),
        )

    async def single_category(self, category_uid: UUID, session: AsyncSession):
        category = await self.get_category_by_uid(category_uid, session)

        if category is None:
            raise NotFound("Expense category not found")

        service_response = ExpCategoryResponseModel.model_validate(category)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[ExpCategoryResponseModel](
                data=service_response, message="Expenses Category retrieved successfully!"
            ).model_dump(),
        )


category_controller = ExpCategoryController()
