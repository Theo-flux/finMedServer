import uuid
from datetime import datetime
from typing import List

from fastapi import status
from fastapi.responses import JSONResponse
from sqlmodel import select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.roles import Role
from src.features.roles.schemas import CreateRole, RoleResponse, RoleStatus, UpdateRole
from src.misc.schemas import ServerRespModel
from src.utils.exceptions import RoleExists, RoleNotFound


class RoleService:
    async def get_role_by_uid(self, role_uid: uuid.UUID, session: AsyncSession):
        statement = select(Role).where(Role.uid == role_uid)
        result = await session.exec(statement=statement)

        return result.first()

    async def get_role_by_name(self, role_name: str, session: AsyncSession):
        statement = select(Role).where(Role.name == role_name.lower())
        result = await session.exec(statement=statement)

        role = result.first()

        return role

    def is_role_active(self, role: Role):
        return False if role.status == RoleStatus.IN_ACTIVE.value else True

    async def role_exists(self, role_uid: uuid.UUID, session: AsyncSession):
        role = self.get_role_by_uid(role_uid, session)

        if role is None:
            return False

        self.is_role_active(role)

    async def create_role(self, role: CreateRole, session: AsyncSession):
        data = role.model_dump()

        if await self.get_role_by_name(data.get("name"), session):
            raise RoleExists()

        new_role = Role(**data)

        session.add(new_role)
        await session.commit()

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=ServerRespModel[bool](data=True, message="Role created!").model_dump(),
        )

    async def update_role(self, role_uid: uuid.UUID, data: UpdateRole, session: AsyncSession):
        role_to_update = await self.get_role_by_uid(role_uid, session)

        if role_to_update is None:
            raise RoleNotFound()

        valid_attrs = data.model_dump(exclude_none=True)

        if valid_attrs:
            valid_attrs["updated_at"] = datetime.now()
            statement = update(Role).where(Role.uid == role_uid).values(**valid_attrs)
            await session.exec(statement=statement)
            await session.commit()
            await session.refresh(role_to_update)

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=ServerRespModel[bool](data=True, message="Role updated!").model_dump(),
        )

    async def get_all_roles(self, session: AsyncSession):
        statement = select(Role)
        result = await session.exec(statement=statement)
        roles = result.all()

        print("result", result)

        role_responses = [RoleResponse.model_validate(role, from_attributes=True) for role in roles]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[List[RoleResponse]](
                data=role_responses, message="Roles retrieved successfully!"
            ).model_dump(),
        )

    async def single_role(self, role_uid: uuid.UUID, session: AsyncSession):
        role = await self.get_role_by_uid(role_uid, session)

        if role is None:
            raise RoleNotFound()

        role_response = RoleResponse.model_validate(role)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[RoleResponse](
                data=role_response, message="Role retrieved successfully!"
            ).model_dump(),
        )
