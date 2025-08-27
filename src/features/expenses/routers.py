from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import Config
from src.db.main import get_session
from src.features.auth.dependencies import AccessTokenBearer
from src.features.expenses.controller import ExpensesController
from src.features.expenses.schemas import (
    CreateExpensesModel,
    EditExpenseModel,
    ExpensesResponseModel,
    SingleExpenseResponseModel,
)
from src.misc.schemas import PaginatedResponseModel, ServerRespModel

expense_router = APIRouter()
expense_controller = ExpensesController()


@expense_router.post("", response_model=ServerRespModel[bool])
async def create_expense(
    data: CreateExpensesModel = Body(...),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await expense_controller.create_exp(token_payload=token_payload, data=data, session=session)


@expense_router.get("", response_model=ServerRespModel[PaginatedResponseModel[ExpensesResponseModel]])
async def get_expenses(
    q: Optional[str] = Query(default=None),
    budget_uid: Optional[UUID] = Query(default=None),
    limit: Optional[int] = Query(
        default=Config.DEFAULT_PAGE_LIMIT, ge=Config.DEFAULT_PAGE_MIN_LIMIT, le=Config.DEFAULT_PAGE_MAX_LIMIT
    ),
    offset: Optional[int] = Query(default=Config.DEFAULT_PAGE_OFFSET, ge=Config.DEFAULT_PAGE_OFFSET),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await expense_controller.get_expenses(
        q=q, budget_uid=budget_uid, limit=limit, offset=offset, token_payload=token_payload, session=session
    )


@expense_router.get("/{exp_uid}", response_model=ServerRespModel[SingleExpenseResponseModel])
async def get_exp_by_uid(
    exp_uid: UUID,
    _: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await expense_controller.single_exp(exp_uid=exp_uid, session=session)


@expense_router.delete("/{exp_uid}", response_model=ServerRespModel[bool])
async def del_exp_by_uid(
    exp_uid: UUID,
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await expense_controller.delete_exp(exp_uid=exp_uid, token_payload=token_payload, session=session)


@expense_router.patch("/{exp_uid}", response_model=ServerRespModel[bool])
async def update_exp(
    exp_uid: UUID,
    data: EditExpenseModel = Body(...),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await expense_controller.update_exp(exp_uid=exp_uid, token_payload=token_payload, data=data, session=session)
