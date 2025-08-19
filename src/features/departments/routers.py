import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.features.departments.schemas import CreateDept, DeptResponse, UpdateDept
from src.features.departments.service import DepartmentService
from src.misc.schemas import ServerRespModel

dept_router = APIRouter()
dept_service = DepartmentService()


@dept_router.get("", response_model=ServerRespModel[List[DeptResponse]])
async def get_all_depts(session: AsyncSession = Depends(get_session)):
    return await dept_service.get_all_depts(session)


@dept_router.get("/{dept_uid}", response_model=ServerRespModel[DeptResponse])
async def get_single_dept(dept_uid: uuid.UUID, session: AsyncSession = Depends(get_session)):
    return await dept_service.single_dept(dept_uid, session)


@dept_router.post("")
async def add_dept(dept: CreateDept, session: AsyncSession = Depends(get_session)):
    return await dept_service.create_dept(dept, session)


@dept_router.patch("/{dept_uid}")
async def update_role(dept_uid: uuid.UUID, data: UpdateDept, session: AsyncSession = Depends(get_session)):
    return await dept_service.update_dept(dept_uid, data, session)
