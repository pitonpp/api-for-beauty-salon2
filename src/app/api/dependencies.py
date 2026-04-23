from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.appointment import AppointmentService, appointment_service
from app.services.auth import auth_service
from app.services.service import ServiceManager, service_manager
from app.services.user import UserService, user_service
from src.app.core.db import get_async_session

SessionDI = Annotated[AsyncSession, Depends(get_async_session)]
AllowAdminDI = Annotated[User, Depends(auth_service.allow_admin_only)]
AllowUserDI = Annotated[User, Depends(auth_service.allow_users)]


def get_appointment_service() -> AppointmentService:
    return appointment_service


def get_user_service() -> UserService:
    return user_service


def get_service_manager() -> ServiceManager:
    return service_manager


AppointmentServiceDI = Annotated[
    AppointmentService, Depends(get_appointment_service)
]
UserServiceDI = Annotated[UserService, Depends(get_user_service)]
ServiceManagerDI = Annotated[ServiceManager, Depends(get_service_manager)]
