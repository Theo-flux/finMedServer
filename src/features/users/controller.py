from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload
from sqlmodel import func, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.users import User
from src.features.users.schemas import UserResponseModel, UserStatus
from src.misc.schemas import PaginatedResponseModel, PaginationModel, ServerRespModel
from src.utils import get_current_and_total_pages
from src.utils.exceptions import NotFound
from src.utils.validators import email_validator, is_email


class UserController:
    async def generate_staff_no(self, dept: str, user_uid: UUID, session: AsyncSession):
        user = await self.get_user_by_uid(user_uid, session)

        dept_prefix = dept.upper().ljust(3, "D")[:3]
        current_year_last_two_digits = str(datetime.now(timezone.utc).year)[2:]
        staff_no = f"{dept_prefix}-{current_year_last_two_digits}-{str(user.id).zfill(4)}"

        statement = update(User).where(User.uid == user_uid).values(staff_no=staff_no)
        await session.exec(statement)

    async def get_user_by_email(self, email: str, session: AsyncSession):
        statement = (
            select(User)
            .options(selectinload(User.department), selectinload(User.role))
            .where(User.email == email.lower())
        )
        result = await session.exec(statement=statement)
        user = result.first()

        return user

    async def get_user_by_staff_no(self, staff_no: str, session: AsyncSession):
        statement = (
            select(User)
            .options(selectinload(User.department), selectinload(User.role))
            .where(User.staff_no == staff_no)
        )
        result = await session.exec(statement=statement)
        user = result.first()

        return user

    async def get_user_by_phone(self, phone_number: str, session: AsyncSession):
        statement = select(User).where(User.phone_number == phone_number)
        result = await session.exec(statement)
        user = result.first()

        return user

    async def get_user_by_uid(self, user_uid: UUID, session: AsyncSession):
        statement = (
            select(User).where(User.uid == user_uid).options(selectinload(User.department), selectinload(User.role))
        )
        result = await session.exec(statement)
        user = result.first()

        return user

    async def get_user_by_mail_or_staff_no(self, email_or_staff_no: str, session: AsyncSession):
        user = None
        if is_email(email_or_staff_no):
            email_validator(email_or_staff_no)
            user = await self.get_user_by_email(email_or_staff_no, session)
        else:
            user = await self.get_user_by_staff_no(email_or_staff_no, session)

        return user

    async def user_exists(self, email_or_phone: str, session: AsyncSession):
        user = (
            self.get_user_by_email(email_or_phone, session)
            if is_email(email_or_phone)
            else self.get_user_by_phone(email_or_phone, session)
        )

        return False if user is None else True

    async def update_last_login(self, user: User, session: AsyncSession):
        setattr(user, "last_login", datetime.now(timezone.utc))

        await session.commit()
        await session.refresh(user)
        return user

    async def update_user(self, user: User, user_data: User, session: AsyncSession):
        allowed_fields = ["first_name", "last_name", "password"]

        for field in allowed_fields:
            value = user_data.get(field)
            if value is not None:
                setattr(user, field, value)

        await session.commit()
        await session.refresh(user)
        return user

    async def single_user(self, user_uid: UUID, session: AsyncSession):
        user = await self.get_user_by_uid(user_uid=user_uid, session=session)

        if not user:
            raise NotFound("User not found")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[UserResponseModel](
                data=UserResponseModel.model_validate(user), message="User retrieved!"
            ).model_dump(),
        )

    async def get_users(
        self,
        user_status: Optional[UserStatus],
        staff_no: Optional[str],
        q: Optional[str],
        limit: Optional[int],
        offset: Optional[int],
        session: AsyncSession,
    ):
        query = select(User).options(selectinload(User.role), selectinload(User.department))

        if q:
            search_term = f"%{q}"
            query = query.where(
                User.first_name.ilike(search_term)
                | User.last_name.ilike(search_term)
                | User.email.ilike(search_term)
                | User.staff_no.ilike(search_term)
            )

        if staff_no:
            query = query.where(User.staff_no == staff_no)

        if user_status:
            query = query.where(User.status == user_status)

        count_query = select(func.count()).select_from(query.subquery())

        total = await session.scalar(count_query)

        query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)

        results = await session.exec(query)

        users = results.all()
        users_response = [UserResponseModel.model_validate(user) for user in users]
        current_page, total_pages = get_current_and_total_pages(
            limit=limit,
            total=total,
            offset=offset,
        )
        paginated_users_response = PaginatedResponseModel.model_validate(
            {
                "items": users_response,
                "pagination": PaginationModel(
                    total=total, current_page=current_page, limit=limit, total_pages=total_pages
                ),
            }
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ServerRespModel[PaginatedResponseModel[UserResponseModel]](
                data=paginated_users_response, message="Users retrieved successfully"
            ).model_dump(),
        )


user_controller = UserController()
