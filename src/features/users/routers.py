import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import Config
from src.db.main import get_session
from src.features.auth.dependencies import RoleBasedTokenBearer
from src.features.users.controller import UserController
from src.features.users.schemas import UserStatus

user_router = APIRouter()
user_controller = UserController()


@user_router.get("/")
async def get_users(
    user_status: Optional[UserStatus] = Query(default=None),
    staff_no: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(
        default=Config.DEFAULT_PAGE_LIMIT, ge=Config.DEFAULT_PAGE_MIN_LIMIT, le=Config.DEFAULT_PAGE_MAX_LIMIT
    ),
    offset: Optional[int] = Query(default=Config.DEFAULT_PAGE_OFFSET, ge=Config.DEFAULT_PAGE_OFFSET),
    _: dict = Depends(RoleBasedTokenBearer(["admin"])),
    session: AsyncSession = Depends(get_session),
):
    return await user_controller.get_users(
        user_status=user_status,
        staff_no=staff_no,
        q=q,
        limit=limit,
        offset=offset,
        session=session,
    )


@user_router.get("/{user_uid}")
async def get_user_by_uid(
    user_uid: uuid.UUID,
    _: dict = Depends(RoleBasedTokenBearer(["admin"])),
    session: AsyncSession = Depends(get_session),
):
    return await user_controller.single_user(user_uid=user_uid, session=session)
