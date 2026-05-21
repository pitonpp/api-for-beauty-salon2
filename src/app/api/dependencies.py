"""DI-зависимости для FastAPI: сессии, сервисы, проверка ролей, конвертеры."""

from typing import Annotated, Type

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.jwt_services import TokenService, token_service
from app.core.types import ModelType, SchemaType
from app.models.user import User
from app.services.appointment import AppointmentService, appointment_service
from app.services.auth import AuthService, auth_service
from app.services.master import MasterManager, master_manager
from app.services.master_service import (
    MasterServiceManager,
    master_service_manager,
)
from app.services.service import ServiceManager, service_manager
from app.services.user import UserService, user_service

SessionDI = Annotated[AsyncSession, Depends(get_async_session)]


AllowAdminDI = Annotated[User, Depends(auth_service.allow_admin_only())]
AllowUserDI = Annotated[User, Depends(auth_service.allow_users())]
AllowMasterAdminDI = Annotated[
    User,
    Depends(auth_service.allow_admin_and_master()),
]


AppointmentServiceDI = Annotated[
    AppointmentService,
    Depends(lambda: appointment_service),
]
UserServiceDI = Annotated[UserService, Depends(lambda: user_service)]
ServiceManagerDI = Annotated[ServiceManager, Depends(lambda: service_manager)]
AuthServiceDI = Annotated[AuthService, Depends(lambda: auth_service)]
TokenServiceDI = Annotated[TokenService, Depends(lambda: token_service)]
MasterManagerDI = Annotated[MasterManager, Depends(lambda: master_manager)]
MasterServiceManagerDI = Annotated[
    MasterServiceManager,
    Depends(lambda: master_service_manager),
]


def to_schema(item: ModelType, schema: Type[SchemaType]) -> SchemaType:
    """Конвертирует модель ORM в Pydantic-схему."""
    return schema.model_validate(item)


def to_schema_list(
    items: list[ModelType],
    schema: Type[SchemaType],
) -> list[SchemaType]:
    """Конвертирует список моделей ORM в список Pydantic-схем."""
    return [schema.model_validate(item) for item in items]
