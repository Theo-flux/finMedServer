import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.features.expenses_category.controller import ExpCategoryController
from src.features.services.schemas import CreateServiceModel, ServiceResponseModel, UpdateServiceModel
from src.misc.schemas import ServerRespModel

category_router = APIRouter()
category_controller = ExpCategoryController()


@category_router.get("", response_model=ServerRespModel[List[ServiceResponseModel]])
async def get_all_categories(session: AsyncSession = Depends(get_session)):
    return await category_controller.get_all_categories(session)


@category_router.get("/{category_uid}", response_model=ServerRespModel[ServiceResponseModel])
async def get_single_role(category_uid: uuid.UUID, session: AsyncSession = Depends(get_session)):
    return await category_controller.single_category(category_uid, session)


@category_router.post("")
async def add_category(category: CreateServiceModel, session: AsyncSession = Depends(get_session)):
    return await category_controller.create_category(category, session)


@category_router.patch("/{category_uid}")
async def update_category(
    service_uid: uuid.UUID, data: UpdateServiceModel, session: AsyncSession = Depends(get_session)
):
    return await category_controller.update_category(service_uid, data, session)
