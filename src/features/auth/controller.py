from typing import Optional

from fastapi import status
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.users import User
from src.db.redis import add_jti_to_block_list
from src.features.departments.controller import DeptController
from src.features.roles.controller import RoleController
from src.features.users.controller import UserController
from src.features.users.schemas import CreateUserModel, LoginUserModel, UserResponseModel
from src.misc.schemas import ServerRespModel
from src.utils.exceptions import InActive, NotFound, UserEmailExists, WrongCredentials
from src.utils.validators import email_validator, is_email

from .authentication import Authentication
from .schemas import ChangePwdModel, TokenModel, TokenUserModel, UserType

user_controller = UserController()
role_controller = RoleController()
dept_controller = DeptController()


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

    async def revoke_token(self, token_payload: dict):
        jti = token_payload["jti"]
        await add_jti_to_block_list(jti)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel(
                data=True,
                message="logged out successfully.",
            ).model_dump(),
        )

    async def new_access_token(self, token_payload: dict):
        new_access_token = Authentication.create_token(TokenUserModel.model_validate(token_payload["user"]))
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel(
                data={"access_token": new_access_token},
                message="new access token generated.",
            ).model_dump(),
        )

    async def change_pwd(self, data: ChangePwdModel, session: AsyncSession):
        user = await user_controller.get_user_by_email(email=data.email, session=session)

        if not user:
            raise NotFound("User doesn't exist.")

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
        user = None
        if is_email(login_data.email_or_staff_no):
            email_validator(login_data.email_or_staff_no)
            user = await user_controller.get_user_by_email(login_data.email_or_staff_no, session)
        else:
            user = await user_controller.get_user_by_staff_no(login_data.email_or_staff_no, session)

        if not user:
            raise NotFound("User doesn't exist.")

        if login_data.password:
            if not user.password:
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=ServerRespModel[TokenModel](
                        data={
                            "access_token": "",
                            "refresh_token": "",
                            "user_type": UserType.NEW_USER.value,
                        },
                        message="user token generated.",
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

                access_token = Authentication.create_token(user_data)
                refresh_token = Authentication.create_token(user_data=user_data, refresh=True)

                await user_controller.update_last_login(user=user, session=session)

                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=ServerRespModel[TokenModel](
                        data={
                            "access_token": access_token,
                            "refresh_token": refresh_token,
                            "user_type": UserType.OLD_USER.value,
                        },
                        message="user token generated.",
                    ).model_dump(),
                )

            raise WrongCredentials()
        else:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=ServerRespModel[TokenModel](
                    data={
                        "access_token": "",
                        "refresh_token": "",
                        "user_type": UserType.OLD_USER.value if user.password else UserType.NEW_USER.value,
                    },
                    message="user token generated.",
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
