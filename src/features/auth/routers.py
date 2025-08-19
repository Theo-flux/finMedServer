from fastapi import APIRouter, Body, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.features.users.schemas import CreateUserModel, LoginUserModel
from src.misc.schemas import ServerRespModel

from .controller import AuthController
from .dependencies import AccessTokenBearer, RefreshTokenBearer
from .schemas import ChangePwdModel, LoginResModel, TokenUserModel

auth_router = APIRouter()
auth_controller = AuthController()


@auth_router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=ServerRespModel[LoginResModel],
)
async def login_user(login_data: LoginUserModel = Body(...), session: AsyncSession = Depends(get_session)):
    return await auth_controller.login_user(login_data, session)


@auth_router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=ServerRespModel[bool],
)
async def register_user(user: CreateUserModel = Body(...), session: AsyncSession = Depends(get_session)):
    return await auth_controller.create_user(user, session)


@auth_router.get(
    "/profile",
    status_code=status.HTTP_200_OK,
    response_model=ServerRespModel[TokenUserModel],
)
async def get_current_user_profile(
    token_payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    return await auth_controller.get_current_user(token_payload, session)


@auth_router.get("/logout")
async def revoke_user_token(token_payload: dict = Depends(AccessTokenBearer())):
    return await auth_controller.revoke_token(token_payload)


@auth_router.get("/new-access-token", status_code=status.HTTP_200_OK, response_model=ServerRespModel)
async def get_new_user_access_token(
    token_payload: dict = Depends(RefreshTokenBearer()),
):
    return await auth_controller.new_access_token(token_payload)


@auth_router.post("/pwd-reset", status_code=status.HTTP_200_OK, response_model=ServerRespModel[bool])
async def pwd_reset(data: ChangePwdModel = Body(...), session: AsyncSession = Depends(get_session)):
    return await auth_controller.change_pwd(data=data, session=session)
