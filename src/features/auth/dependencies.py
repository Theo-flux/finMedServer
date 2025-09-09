import logging
from typing import List, Optional, Union

from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import select

from src.db.main import AsyncSessionMaker
from src.db.models.roles import Role
from src.db.redis import token_in_block_list
from src.features.auth.authentication import Authentication
from src.features.roles.controller import RoleController
from src.features.roles.schemas import RoleStatus
from src.utils.exceptions import (
    AccessTokenRequired,
    InsufficientPermissions,
    InvalidToken,
    NotFound,
    RefreshTokenExpired,
    RefreshTokenRequired,
    TokenExpired,
)


class TokenBearer(HTTPBearer):
    def __init__(self, auto_error=True, is_not_protected: bool = False):
        self.is_not_protected = is_not_protected
        super().__init__(
            auto_error=auto_error,
        )

    async def is_token_valid(self, token: str) -> bool:
        try:
            token_payload = Authentication.decode_token(token)

            if await token_in_block_list(token_payload["jti"]):
                raise InvalidToken()
        except RefreshTokenExpired as e:
            logging.warning(f"RefreshTokenExpired caught in is_token_valid: {e}")
            raise
        except TokenExpired as e:
            logging.warning(f"TokenExpired caught in is_token_valid: {e}")
            raise
        except Exception as e:
            logging.warning(f"Other exception in is_token_valid: {type(e).__name__}: {e}")
            return False

    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        auth_header = request.headers.get("Authorization")

        if self.is_not_protected and not auth_header:
            return None

        cred = await super().__call__(request)
        token = cred.credentials

        self.is_token_valid(token)

        token_payload = Authentication.decode_token(token)
        await self.verify_token_data(token_payload)

        return token_payload

    async def verify_token_data(self, token_payload) -> None:
        raise NotImplementedError("Please override this method in child classes.")


class AccessTokenBearer(TokenBearer):
    async def verify_token_data(self, token_payload):
        if token_payload and token_payload["refresh"]:
            raise AccessTokenRequired()


class RefreshTokenBearer(TokenBearer):
    async def verify_token_data(self, token_payload):
        if token_payload and not token_payload["refresh"]:
            raise RefreshTokenRequired()


class RoleBasedTokenBearer(AccessTokenBearer):
    def __init__(
        self,
        required_roles: Union[str, List[str]],
        auto_error: bool = True,
        check_role_status: bool = True,
        is_not_protected: bool = False,
    ):
        super().__init__(auto_error=auto_error, is_not_protected=is_not_protected)
        if isinstance(required_roles, str):
            self.required_roles = [required_roles]
        else:
            self.required_roles = required_roles or []

        self.check_role_status = check_role_status

    async def get_active_roles_from_db(self, role_names: List[str]):
        if not role_names or not self.check_role_status:
            return role_names

        async with AsyncSessionMaker() as session:
            statement = select(Role).where(Role.name.in_(role_names), Role.status == RoleStatus.ACTIVE.value)
            active_roles = await session.exec(statement=statement)

            return [role.name for role in active_roles]

    async def verify_token_data(self, token_payload):
        if token_payload and token_payload["refresh"]:
            raise AccessTokenRequired()

        if not self.required_roles:
            return

        active_required_roles = self.required_roles

        if self.check_role_status:
            valid_required_roles = await self.get_active_roles_from_db(self.required_roles)
            if not valid_required_roles:
                raise NotFound(f"None of the required roles {self.required_roles} are active in the system")

            active_required_roles = valid_required_roles

        role_uid = token_payload["user"]["role_uid"]
        if not role_uid:
            raise NotFound("Role not found.")

        async with AsyncSessionMaker() as session:
            role = await RoleController().get_role_by_uid(role_uid, session)

            if role is None:
                raise NotFound("Role not found.")

            if role.name not in active_required_roles:
                raise InsufficientPermissions()


class AdminTokenBearer(RoleBasedTokenBearer):
    def __init__(self, auto_error=True, check_role_status=True):
        super().__init__(required_roles=["admin"], auto_error=auto_error, check_role_status=check_role_status)


class AllAdminsTokenBearer(RoleBasedTokenBearer):
    def __init__(self, auto_error=True, check_role_status=True):
        super().__init__(
            required_roles=["admin", "subadmin"], auto_error=auto_error, check_role_status=check_role_status
        )
