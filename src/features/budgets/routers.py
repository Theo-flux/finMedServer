import uuid
from typing import Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import Config
from src.db.main import get_session
from src.features.auth.dependencies import AccessTokenBearer
from src.features.budgets.controller import BudgetControllers
from src.features.budgets.schemas import CreateBudgetModel, EditBudgetModel
from src.misc.schemas import ServerRespModel

budget_router = APIRouter()
budget_controller = BudgetControllers()


@budget_router.get("/{budget_uid}")
async def get_budget_by_uid(
    budget_uid: uuid.UUID,
    _: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await budget_controller.single_budget(budget_uid=budget_uid, session=session)


@budget_router.get("/my_budgets")
async def get_user_budgets(
    limit: Optional[int] = Query(default=Config.DEFAULT_PAGE_LIMIT),
    next_cursor: Optional[int] = Query(default=None),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await budget_controller.get_my_budget(
        limit=limit, next_cursor=next_cursor, token_payload=token_payload, session=session
    )


@budget_router.get("/assigned")
async def get_assigned_budgets(_: dict = Depends(AccessTokenBearer()), session: AsyncSession = Depends(get_session)):
    pass


@budget_router.post("", response_model=ServerRespModel[bool])
async def create_budget(
    data: CreateBudgetModel = Body(...),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await budget_controller.create_budget(token_payload=token_payload, data=data, session=session)


@budget_router.patch("/{budget_uid}", response_model=ServerRespModel[bool])
async def update_budget(
    budget_uid: str,
    data: EditBudgetModel = Body(...),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await budget_controller.update_budget(
        budget_uid=budget_uid, token_payload=token_payload, data=data, session=session
    )
