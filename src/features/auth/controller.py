from typing import Optional

from fastapi import status
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.users import User
from src.db.redis import add_jti_to_block_list, redis_client
from src.features.departments.controller import dept_controller
from src.features.roles.controller import role_controller
from src.features.users.controller import user_controller
from src.features.users.schemas import CreateUserModel, LoginUserModel, UserResponseModel
from src.misc.schemas import ServerRespModel
from src.utils.exceptions import (
    InActive,
    InvalidToken,
    NotFound,
    RefreshTokenExpired,
    RefreshTokenRequired,
    TokenExpired,
    UserEmailExists,
    WrongCredentials,
)
from src.utils.logger import setup_logger

from .authentication import Authentication
from .schemas import ChangePwdModel, TokenModel, TokenUserModel, UserType

logger = setup_logger(__name__)


class AuthController:
    async def get_current_user(self, token_payload: dict, session: AsyncSession):
        user_email = token_payload["user"]["email"]
        user = await user_controller.get_user_by_email(user_email, session)

        if not user:
            raise NotFound("User doesn't exist.")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[UserResponseModel](
                data=UserResponseModel.model_validate(user).model_dump(),
                message="user profile retrieved",
            ).model_dump(mode="json"),
        )

    async def revoke_token(self, refresh_token_jti: Optional[str], token_payload: dict):
        jti = token_payload["jti"]
        await add_jti_to_block_list(jti)

        if refresh_token_jti:
            await add_jti_to_block_list(refresh_token_jti)
            response = await redis_client.client.delete(refresh_token_jti)
            print("Deleted refresh token:", response)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel(
                data=True,
                message="logged out successfully.",
            ).model_dump(),
        )

    async def new_access_token(self, token_jti: str, session: AsyncSession):
        if not token_jti:
            raise RefreshTokenRequired("Refresh token not found.")

        try:
            # first get the token from redis and compare with the provided token
            refresh_token = await redis_client.client.get(token_jti)

            if not refresh_token:
                raise RefreshTokenExpired("Refresh token invalid or expired.")

            payload = await Authentication.decode_token(refresh_token)

            if not payload.get("refresh", False):
                raise RefreshTokenExpired("Invalid token type.")

            user_data = payload["user"]

            user = await user_controller.get_user_by_uid(user_data["uid"], session=session)

            if not user:
                raise RefreshTokenExpired("Refresh token invalid or expired.")

            new_access_token = await Authentication.create_token(
                user_data=TokenUserModel.model_validate(
                    {
                        "id": user.id,
                        "uid": user.uid,
                        "staff_no": user.staff_no,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "status": user.status,
                        "role_uid": user.role_uid,
                        "department_uid": user.department_uid,
                    }
                )
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=ServerRespModel[TokenModel](
                    data={
                        "access_token": new_access_token,
                        "user_type": UserType.OLD_USER.value,
                    },
                    message="new access token generated.",
                ).model_dump(),
            )
        except (RefreshTokenRequired, RefreshTokenExpired, InvalidToken, TokenExpired):
            raise
        except Exception as e:
            logger.error(f"Error generating new access token: {e}")
            raise

    async def change_pwd(self, data: ChangePwdModel, session: AsyncSession):
        user = await user_controller.get_user_by_mail_or_staff_no(
            email_or_staff_no=data.email_or_staff_no, session=session
        )

        if not user:
            raise NotFound("User doesn't exist.")

        if user.password and not Authentication.verify_password(data.old_password, user.password):
            raise WrongCredentials("Old password is incorrect.")

        if user.password and Authentication.verify_password(data.new_password, user.password):
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=ServerRespModel[bool](
                    data=False, message="New password cannot be same as old password."
                ).model_dump(),
            )

        await user_controller.update_user(
            user=user,
            user_data={"password": Authentication.generate_password_hash(data.model_dump().get("new_password"))},
            session=session,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[bool](data=True, message="Password reset successful.").model_dump(),
        )

    async def login_user(self, login_data: LoginUserModel, session: AsyncSession):
        user = await user_controller.get_user_by_mail_or_staff_no(
            email_or_staff_no=login_data.email_or_staff_no, session=session
        )

        if not user:
            raise NotFound("User doesn't exist.")

        if login_data.password:
            if not user.password:
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=ServerRespModel[TokenModel](
                        data={
                            "access_token": "",
                            "user_type": UserType.NEW_USER.value,
                        },
                        message="user token not generated.",
                    ).model_dump(),
                )

            if Authentication.verify_password(login_data.password, user.password):
                user_data = TokenUserModel.model_validate(
                    {
                        "id": user.id,
                        "uid": user.uid,
                        "staff_no": user.staff_no,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "status": user.status,
                        "role_uid": user.role_uid,
                        "department_uid": user.department_uid,
                    }
                )

                access_token = await Authentication.create_token(user_data)
                await user_controller.update_last_login(user=user, session=session)

                response = JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=ServerRespModel[TokenModel](
                        data={
                            "access_token": access_token,
                            "user_type": UserType.OLD_USER.value,
                        },
                        message="user token generated.",
                    ).model_dump(),
                )

                await Authentication.create_token(user_data=user_data, refresh=True, response=response)

                return response

            raise WrongCredentials()
        else:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=ServerRespModel[TokenModel](
                    data={
                        "access_token": "",
                        "user_type": UserType.OLD_USER.value if user.password else UserType.NEW_USER.value,
                    },
                    message="user token not generated.",
                ).model_dump(),
            )

    async def create_user(self, token_payload: Optional[dict], user_data: CreateUserModel, session: AsyncSession):
        user = user_data.model_dump()

        if await user_controller.get_user_by_email(user.get("email"), session):
            raise UserEmailExists()

        if await role_controller.role_exists(user.get("role_uid"), session) is False:
            raise InActive("Role is inactive.")

        dept = await dept_controller.dept_exists(user.get("department_uid"), session)

        if dept is None:
            raise InActive("Department is inactive.")

        if token_payload:
            user["created_by_uid"] = token_payload["user"]["uid"]

        if user.get("password"):
            user["password"] = Authentication.generate_password_hash(user["password"])

        try:
            new_user = User(**user)
            session.add(new_user)
            await session.flush()

            await user_controller.generate_staff_no(dept.name, new_user.uid, session)

            await session.commit()

        except Exception as e:
            await session.rollback()
            raise e

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=ServerRespModel[bool](data=True, message="User created!").model_dump(),
        )

    async def forgot_password(self, email_staff_no: str, session: AsyncSession):
        user = await user_controller.get_user_by_mail_or_staff_no(email_or_staff_no=email_staff_no, session=session)

        if not user:
            raise NotFound("User doesn't exist.")

        # TODO: send email with reset link

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[bool](
                data=True, message="Password reset initiated. Please check your email."
            ).model_dump(),
        )
