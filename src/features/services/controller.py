from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import status
from fastapi.responses import JSONResponse
from sqlmodel import select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.services import Service
from src.features.services.schemas import CreateServiceModel, ServiceResponseModel, ServiceStatus, UpdateServiceModel
from src.misc.schemas import ServerRespModel
from src.utils.exceptions import NotFound, ResourceExists


class ServiceController:
    async def get_service_by_uid(self, service_uid: UUID, session: AsyncSession):
        statement = select(Service).where(Service.uid == service_uid)
        result = await session.exec(statement=statement)

        return result.first()

    async def get_service_by_name(self, service_name: str, session: AsyncSession):
        statement = select(Service).where(Service.name == service_name.lower())
        result = await session.exec(statement=statement)

        service = result.first()

        return service

    def is_service_active(self, service: Service):
        return False if service.status == ServiceStatus.IN_ACTIVE.value else True

    async def service_exists(self, service_uid: UUID, session: AsyncSession):
        service = self.get_service_by_uid(service_uid, session)

        if service is None:
            return False

        self.is_service_active(service)

    async def create_service(self, service: CreateServiceModel, session: AsyncSession):
        data = service.model_dump()

        if await self.get_service_by_name(data.get("name"), session):
            raise ResourceExists("Service exists.")

        new_service = Service(**data)

        session.add(new_service)
        await session.commit()

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=ServerRespModel[bool](data=True, message="Service created!").model_dump(),
        )

    async def update_service(self, service_uid: UUID, data: UpdateServiceModel, session: AsyncSession):
        service_to_update = await self.get_service_by_uid(service_uid, session)

        if service_to_update is None:
            raise NotFound("Service not found")

        valid_attrs = data.model_dump(exclude_none=True)

        if valid_attrs:
            valid_attrs["updated_at"] = datetime.now()
            statement = update(Service).where(Service.uid == service_uid).values(**valid_attrs)
            await session.exec(statement=statement)
            await session.commit()
            await session.refresh(service_to_update)

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=ServerRespModel[bool](data=True, message="Service updated!").model_dump(),
        )

    async def get_all_services(self, session: AsyncSession):
        statement = select(Service)
        result = await session.exec(statement=statement)
        services = result.all()

        service_responses = [ServiceResponseModel.model_validate(service, from_attributes=True) for service in services]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[List[ServiceResponseModel]](
                data=service_responses, message="Services retrieved successfully!"
            ).model_dump(),
        )

    async def single_service(self, service_uid: UUID, session: AsyncSession):
        service = await self.get_service_by_uid(service_uid, session)

        if service is None:
            raise NotFound("Service not found")

        service_response = ServiceResponseModel.model_validate(service)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[ServiceResponseModel](
                data=service_response, message="Service retrieved successfully!"
            ).model_dump(),
        )


service_controller = ServiceController()
