from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt_services import TokenService, token_service
from app.models.user import User
from app.services.appointment import AppointmentService, appointment_service
from app.services.auth import AuthService, auth_service
from app.services.service import ServiceManager, service_manager
from app.services.user import UserService, user_service
from src.app.core.db import get_async_session

SessionDI = Annotated[AsyncSession, Depends(get_async_session)]

AllowAdminDI = Annotated[User, Depends(auth_service.allow_admin_only)]
AllowUserDI = Annotated[User, Depends(auth_service.allow_users)]

AppointmentServiceDI = Annotated[
    AppointmentService, Depends(lambda: appointment_service)
]
UserServiceDI = Annotated[UserService, Depends(lambda: user_service)]
ServiceManagerDI = Annotated[ServiceManager, Depends(lambda: service_manager)]
AuthServiceDI = Annotated[AuthService, Depends(lambda: auth_service)]
TokenServiceDI = Annotated[TokenService, Depends(lambda: token_service)]
