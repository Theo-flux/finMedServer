from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.features.services.controller import service_controller
from src.features.services.schemas import CreateServiceModel, ServiceResponseModel, UpdateServiceModel
from src.misc.schemas import ServerRespModel

service_router = APIRouter()


@service_router.get("", response_model=ServerRespModel[List[ServiceResponseModel]])
async def get_all_roles(session: AsyncSession = Depends(get_session)):
    return await service_controller.get_all_services(session)


@service_router.get("/{service_uid}", response_model=ServerRespModel[ServiceResponseModel])
async def get_single_role(service_uid: UUID, session: AsyncSession = Depends(get_session)):
    return await service_controller.single_service(service_uid, session)


@service_router.post("")
async def add_role(role: CreateServiceModel, session: AsyncSession = Depends(get_session)):
    return await service_controller.create_service(role, session)


@service_router.patch("/{service_uid}")
async def update_role(service_uid: UUID, data: UpdateServiceModel, session: AsyncSession = Depends(get_session)):
    return await service_controller.update_service(service_uid, data, session)
