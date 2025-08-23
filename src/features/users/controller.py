import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import selectinload
from sqlmodel import select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.users import User
from src.utils.validators import is_email


class UserController:
    async def generate_staff_no(self, dept: str, user_uid: uuid.UUID, session: AsyncSession):
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

    async def get_user_by_phone(self, phone_number: str, session: AsyncSession):
        statement = select(User).where(User.phone_number == phone_number)
        result = await session.exec(statement)
        user = result.first()

        return user

    async def get_user_by_uid(self, user_uid: uuid.UUID, session: AsyncSession):
        statement = select(User).where(User.uid == user_uid)
        result = await session.exec(statement)
        user = result.first()

        return user

    async def user_exists(self, email_or_phone: str, session: AsyncSession):
        user = (
            self.get_user_by_email(email_or_phone, session)
            if is_email(email_or_phone)
            else self.get_user_by_phone(email_or_phone, session)
        )

        return False if user is None else True

    async def update_user(self, user: User, user_data: dict, session: AsyncSession):
        allowed_fields = ["first_name", "last_name", "password"]

        for field in allowed_fields:
            value = user_data.get(field)
            if value is not None:
                setattr(user, field, value)

        await session.commit()
        await session.refresh(user)
        return user

    async def get_all_users(self, session: AsyncSession):
        pass
