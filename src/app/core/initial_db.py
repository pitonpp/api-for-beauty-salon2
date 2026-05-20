from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.user import user_service
from app.schemas.status_enum import UserRole
from app.schemas.user import UserAdminCreate


async def create_first_users(session: AsyncSession) -> None:
    users_data = [
        {
            "phone": settings.first_superuser_phonenumber,
            "username": settings.first_superuser_username,
            "password": settings.first_superuser_password,
            "first_name": settings.first_superuser_first_name,
            "last_name": settings.first_superuser_last_name,
            "role": UserRole.ADMIN,
        },
        {
            "phone": settings.first_master_phonenumber,
            "username": settings.first_master_username,
            "password": settings.first_master_password,
            "first_name": settings.first_master_first_name,
            "last_name": settings.first_master_last_name,
            "role": UserRole.MASTER,
        },
        {
            "phone": settings.first_user_phonenumber,
            "username": settings.first_user_username,
            "password": settings.first_user_password,
            "first_name": settings.first_user_first_name,
            "last_name": settings.first_user_last_name,
            "role": UserRole.USER,
        },
    ]

    for data in users_data:
        existing_user = await user_service.crud.get_one_by(
            session,
            username=data["username"],
            phone=data["phone"],
        )

        if existing_user:
            print("Пользователь уже существует")
            continue

        user = UserAdminCreate(
            phone=data["phone"],
            username=data["username"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            role=data["role"],
        )
        await user_service.create_user(session, user)
