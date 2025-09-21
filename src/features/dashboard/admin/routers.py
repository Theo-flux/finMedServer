from typing import List

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.features.auth.dependencies import RoleBasedTokenBearer
from src.features.dashboard.admin.schema import BudgetUtilizationModel, PeriodicAnalyticsParams
from src.misc.schemas import ServerRespModel

from .controller import admin_controller

admin_router = APIRouter()


@admin_router.get("/income")
@admin_router.get("/budget_utilization_by_department", response_model=ServerRespModel[List[BudgetUtilizationModel]])
async def get_budget_utilization(
    params: PeriodicAnalyticsParams = Depends(),
    _: dict = Depends(RoleBasedTokenBearer(["admin"])),
    session: AsyncSession = Depends(get_session),
):
    """
    Get budget utilization by department.

    Query Parameters:
    - month_range: Number of months to analyze (1, 3, 6, 12)
    - end_month: End month (1-12)
    - end_year: End year
    """
    result = await admin_controller.budget_utilization_by_department(params, session)
    return ServerRespModel(data=result, message="Budget utilization retrieved successfully")
