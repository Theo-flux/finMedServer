import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.features.services.controller import ServiceController
from src.features.services.schemas import CreateServiceModel, ServiceResponseModel, UpdateServiceModel
from src.misc.schemas import ServerRespModel

service_router = APIRouter()
role_controller = ServiceController()


@service_router.get("", response_model=ServerRespModel[List[ServiceResponseModel]])
async def get_all_roles(session: AsyncSession = Depends(get_session)):
    return await role_controller.get_all_services(session)


@service_router.get("/{service_uid}", response_model=ServerRespModel[ServiceResponseModel])
async def get_single_role(service_uid: uuid.UUID, session: AsyncSession = Depends(get_session)):
    return await role_controller.single_service(service_uid, session)


@service_router.post("")
async def add_role(role: CreateServiceModel, session: AsyncSession = Depends(get_session)):
    return await role_controller.create_service(role, session)


@service_router.patch("/{service_uid}")
async def update_role(service_uid: uuid.UUID, data: UpdateServiceModel, session: AsyncSession = Depends(get_session)):
    return await role_controller.update_service(service_uid, data, session)
