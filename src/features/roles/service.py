import uuid
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

        role = result.first()

        return role

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
        role = self.get_role_by_name(role.name, session)

        if role is not None:
            raise RoleExists()

        new_role = Role(**role)

        await session.add(new_role)
        session.commit()

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=ServerRespModel[bool](data=True, message="Role created!").model_dump(),
        )

    async def update_role(self, role_uid: uuid.UUID, role: UpdateRole, session: AsyncSession):
        role_to_update = await self.get_role_by_uid(role_uid, session)

        if role_to_update is None:
            raise RoleNotFound()

        valid_attrs = role.model_dump(exclude_none=True)

        if valid_attrs:
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

        role_responses = [RoleResponse.model_validate(role) for role in roles]

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=ServerRespModel[List[RoleResponse]](
                data=role_responses, message="Roles retrieved successfully!"
            ).model_dump(),
        )
