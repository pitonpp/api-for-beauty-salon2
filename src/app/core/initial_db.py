from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.status_enum import UserRole
from app.schemas.user import UserAdminCreate
from app.services.user import user_service


async def create_first_users(session: AsyncSession) -> None:
    """Создаёт начальных пользователей (admin, master, user) при запуске."""
    users_data = [
        {
            "phone": settings.first_superuser_phonenumber,
            "username": settings.first_superuser_username,
            "email": settings.first_superuser_email,
            "password": settings.first_superuser_password,
            "first_name": settings.first_superuser_first_name,
            "last_name": settings.first_superuser_last_name,
            "role": UserRole.ADMIN,
        },
        {
            "phone": settings.first_master_phonenumber,
            "username": settings.first_master_username,
            "email": settings.first_master_email,
            "password": settings.first_master_password,
            "first_name": settings.first_master_first_name,
            "last_name": settings.first_master_last_name,
            "role": UserRole.MASTER,
        },
        {
            "phone": settings.first_user_phonenumber,
            "username": settings.first_user_username,
            "email": settings.first_user_email,
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
            email=data["email"],
        )
        await user_service.create_user(session, user)
