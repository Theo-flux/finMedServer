import uuid
from datetime import datetime
from typing import List

from fastapi import status
from fastapi.responses import JSONResponse
from sqlmodel import select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.departments import Department
from src.features.departments.schemas import CreateDept, DepartmentStatus, DeptResponse, UpdateDept
from src.misc.schemas import ServerRespModel
from src.utils.exceptions import DeptExists, DeptNotFound


class DeptController:
    def generate_staff_no(self, dept: str):
        # TODO:
        # 1. Format (<first three letters of dept.>-<year>-<id padded with two zeros.)
        # 2. Ensure the department exists and the department status is active.
        # 3. Ensure to generate a unique staff no.
        pass

    async def get_dept_by_uid(self, dept_uid: uuid.UUID, session: AsyncSession):
        statement = select(Department).where(Department.uid == dept_uid)
        result = await session.exec(statement=statement)

        return result.first()

    async def get_dept_by_name(self, dept_name: str, session: AsyncSession):
        statement = select(Department).where(Department.name == dept_name.lower())
        result = await session.exec(statement=statement)

        return result.first()

    def is_dept_active(self, dept: Department):
        return False if dept.status == DepartmentStatus.IN_ACTIVE.value else True

    async def dept_exists(self, dept_uid: uuid.UUID, session: AsyncSession):
        dept = await self.get_dept_by_uid(dept_uid, session)

        if dept is None:
            return False

        self.is_dept_active(dept)

        return True

    async def create_dept(self, dept: CreateDept, session: AsyncSession):
        data = dept.model_dump()

        if await self.get_dept_by_name(data.get("name"), session):
            raise DeptExists()

        new_dept = Department(**data)

        session.add(new_dept)
        await session.commit()

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=ServerRespModel[bool](data=True, message="Dept. created!").model_dump(),
        )

    async def update_dept(self, dept_uid: uuid.UUID, data: UpdateDept, session: AsyncSession):
        dept_to_update = await self.get_dept_by_uid(dept_uid, session)

        if dept_to_update is None:
            raise DeptNotFound()

        valid_attrs = data.model_dump(exclude_none=True)

        if valid_attrs:
            valid_attrs["updated_at"] = datetime.now()
            statement = update(Department).where(Department.uid == dept_uid).values(**valid_attrs)
            await session.exec(statement=statement)
            await session.commit()
            await session.refresh(dept_to_update)

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=ServerRespModel[bool](data=True, message="Department updated!").model_dump(),
        )

    async def get_all_depts(self, session: AsyncSession):
        statement = select(Department)
        result = await session.exec(statement=statement)
        roles = result.all()

        print("result", result)

        role_responses = [DeptResponse.model_validate(role, from_attributes=True) for role in roles]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[List[DeptResponse]](
                data=role_responses, message="Depts. retrieved successfully!"
            ).model_dump(),
        )

    async def single_dept(self, dept_uid: uuid.UUID, session: AsyncSession):
        role = await self.get_dept_by_uid(dept_uid, session)

        if role is None:
            raise DeptNotFound()

        role_response = DeptResponse.model_validate(role)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[DeptResponse](
                data=role_response, message="Depts. retrieved successfully!"
            ).model_dump(),
        )
