from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import Config
from src.db.main import get_session
from src.features.auth.dependencies import AccessTokenBearer
from src.features.budgets.controller import BudgetController
from src.features.budgets.schemas import BudgetAvailability, BudgetStatus, CreateBudgetModel, EditBudgetModel
from src.misc.schemas import ServerRespModel

budget_router = APIRouter()
budget_controller = BudgetController()


@budget_router.post("", response_model=ServerRespModel[bool])
async def create_budget(
    data: CreateBudgetModel = Body(...),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await budget_controller.create_budget(token_payload=token_payload, data=data, session=session)


@budget_router.get("/user_budgets")
async def get_user_budgets(
    q: Optional[str] = Query(default=None),
    budget_status: Optional[BudgetStatus] = Query(default=None),
    budget_availability: Optional[BudgetAvailability] = Query(default=None),
    limit: Optional[int] = Query(
        default=Config.DEFAULT_PAGE_LIMIT, ge=Config.DEFAULT_PAGE_MIN_LIMIT, le=Config.DEFAULT_PAGE_MAX_LIMIT
    ),
    offset: Optional[int] = Query(default=Config.DEFAULT_PAGE_OFFSET, ge=Config.DEFAULT_PAGE_OFFSET),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await budget_controller.get_user_budget(
        q=q,
        limit=limit,
        budget_status=budget_status,
        budget_availability=budget_availability,
        offset=offset,
        token_payload=token_payload,
        session=session,
    )


@budget_router.get("/user_assigned_budgets")
async def get_assigned_budgets(
    q: Optional[str] = Query(default=None),
    budget_status: Optional[BudgetStatus] = Query(default=None),
    budget_availability: Optional[BudgetAvailability] = Query(default=None),
    limit: Optional[int] = Query(
        default=Config.DEFAULT_PAGE_LIMIT, ge=Config.DEFAULT_PAGE_MIN_LIMIT, le=Config.DEFAULT_PAGE_MAX_LIMIT
    ),
    offset: Optional[int] = Query(default=Config.DEFAULT_PAGE_OFFSET, ge=Config.DEFAULT_PAGE_OFFSET),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await budget_controller.get_assigned_budget(
        q=q,
        limit=limit,
        budget_status=budget_status,
        budget_availability=budget_availability,
        offset=offset,
        token_payload=token_payload,
        session=session,
    )


@budget_router.get("/{budget_uid}")
async def get_budget_by_uid(
    budget_uid: UUID,
    _: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await budget_controller.single_budget(budget_uid=budget_uid, session=session)


@budget_router.delete("/{budget_uid}")
async def del_budget_by_uid(
    budget_uid: UUID,
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await budget_controller.delete_budget(budget_uid=budget_uid, token_payload=token_payload, session=session)


@budget_router.patch("/{budget_uid}", response_model=ServerRespModel[bool])
async def update_budget(
    budget_uid: UUID,
    data: EditBudgetModel = Body(...),
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await budget_controller.update_budget(
        budget_uid=budget_uid, token_payload=token_payload, data=data, session=session
    )
