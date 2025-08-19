import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.features.roles.schemas import CreateRole, RoleResponse, UpdateRole
from src.features.roles.service import RoleService
from src.misc.schemas import ServerRespModel

role_router = APIRouter()
role_service = RoleService()


@role_router.get("", response_model=ServerRespModel[List[RoleResponse]])
async def get_all_roles(session: AsyncSession = Depends(get_session)):
    return await role_service.get_all_roles(session)


@role_router.get("/{role_uid}", response_model=ServerRespModel[RoleResponse])
async def get_single_role(role_uid: uuid.UUID, session: AsyncSession = Depends(get_session)):
    return await role_service.single_role(role_uid, session)


@role_router.post("")
async def add_role(role: CreateRole, session: AsyncSession = Depends(get_session)):
    return await role_service.create_role(role, session)


@role_router.patch("/{role_uid}")
async def update_role(role_uid: uuid.UUID, data: UpdateRole, session: AsyncSession = Depends(get_session)):
    return await role_service.update_role(role_uid, data, session)
