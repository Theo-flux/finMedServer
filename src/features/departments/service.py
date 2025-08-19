import uuid

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.departments import Department
from src.features.roles.schemas import RoleStatus


class DepartmentService:
    async def dept_exists(self, dept_uid: uuid.UUID, session: AsyncSession):
        statement = select(Department).where(Department.uid == dept_uid)
        result = await session.exec(statement=statement)

        role = result.first()

        # 1. Ensure the role exists.
        if role is None:
            return False

        # 2. Ensure the role status is active.
        if role.status == RoleStatus.IN_ACTIVE.value:
            return False

        return True

    async def generate_staff_no(self, dept_uid: uuid.UUID, session: AsyncSession):
        # TODO:
        # 1. Ensure the role exists and the role status is active.
        # 2. Ensure the department exists and the department status is active.
        # 3. Ensure to generate a unique staff no.
        pass
