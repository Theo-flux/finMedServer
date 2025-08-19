from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.features.roles.service import RoleService

role_router = APIRouter()
role_service = RoleService()


@role_router.get("")
async def get_all_roles(session: AsyncSession = Depends(get_session)):
    return await role_service.get_all_roles(session)
