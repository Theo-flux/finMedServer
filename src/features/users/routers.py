import uuid

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.features.auth.dependencies import AccessTokenBearer

user_router = APIRouter()


@user_router.get("/{user_uid}")
async def get_user_by_uid(
    user_uid: uuid.UUID,
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    pass
