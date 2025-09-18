from typing import Optional

from fastapi import APIRouter, Body, Cookie, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.features.users.schemas import CreateUserModel, LoginUserModel, UserResponseModel
from src.misc.schemas import ServerRespModel

from .controller import AuthController
from .dependencies import AccessTokenBearer, RoleBasedTokenBearer
from .schemas import ChangePwdModel, TokenModel

auth_router = APIRouter()
auth_controller = AuthController()


@auth_router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=ServerRespModel[TokenModel],
)
async def login_user(login_data: LoginUserModel = Body(...), session: AsyncSession = Depends(get_session)):
    return await auth_controller.login_user(login_data=login_data, session=session)


@auth_router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=ServerRespModel[bool],
)
async def register_user(
    user_data: CreateUserModel = Body(...),
    token_payload: dict = Depends(RoleBasedTokenBearer(required_roles=["admin", "subadmin"], is_not_protected=True)),
    session: AsyncSession = Depends(get_session),
):
    return await auth_controller.create_user(user_data=user_data, token_payload=token_payload, session=session)


@auth_router.get(
    "/profile",
    status_code=status.HTTP_200_OK,
    response_model=ServerRespModel[UserResponseModel],
)
async def get_current_user_profile(
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await auth_controller.get_current_user(token_payload=token_payload, session=session)


@auth_router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    response_model=ServerRespModel[bool],
)
async def revoke_user_token(
    refresh_token_jti: Optional[str] = Cookie(None, alias="refresh_token"),
    token_payload: dict = Depends(AccessTokenBearer()),
):
    return await auth_controller.revoke_token(refresh_token_jti=refresh_token_jti, token_payload=token_payload)


@auth_router.post(
    "/new-access-token",
    status_code=status.HTTP_200_OK,
    response_model=ServerRespModel[TokenModel],
)
async def get_new_user_access_token(
    token_jti: Optional[str] = Cookie(None, alias="refresh_token"), session: AsyncSession = Depends(get_session)
):
    return await auth_controller.new_access_token(token_jti=token_jti, session=session)


@auth_router.post("/pwd-reset", status_code=status.HTTP_200_OK, response_model=ServerRespModel[bool])
async def pwd_reset(data: ChangePwdModel = Body(...), session: AsyncSession = Depends(get_session)):
    return await auth_controller.change_pwd(data=data, session=session)


@auth_router.post("/forgot-pwd", status_code=status.HTTP_200_OK, response_model=ServerRespModel[bool])
async def forgot_password(email: str = Body(..., embed=True), session: AsyncSession = Depends(get_session)):
    return await auth_controller.forgot_password(email=email, session=session)
