from typing import Any

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import SELF_DEACTIVATE
from app.crud.user import CRUDUser, user_crud
from app.models.user import User
from app.schemas import UserCreate, UserUpdate, UserUpdateAdmin

from .base import BaseService
from .password import hash_password


class UserService(BaseService[User, CRUDUser]):
    """Сервис для управления пользователями."""

    model = User

    def __init__(self, crud: CRUDUser) -> None:
        super().__init__(crud)

    def _add_password_hash(self, data: dict[str, Any]) -> dict[str, Any]:
        """Хэширует пароль в переданных данных, если он указан."""

        if "password" not in data or data["password"] is None:
            logger.info("Пароль не указан, пропускаем добавление пароля")
            return data

        data = data.copy()
        data["password"] = hash_password(data["password"])
        return data

    async def create_user(
        self, session: AsyncSession, request: UserCreate
    ) -> User:
        """Создаёт нового пользователя с хэшированным паролем."""

        try:
            request_data = request.model_dump()
            request_data = self._add_password_hash(request_data)

            user = await self.crud.create(request_data, session)
            logger.info(
                "Создан пользователь user_id={} username={} email={}",
                user.id,
                request.username,
                request.email,
            )
            return user

        except IntegrityError as e:
            await session.rollback()
            self._handle_integrity_error(e, "create")

    async def update_user(
        self,
        user_id: int,
        session: AsyncSession,
        request: UserUpdate | UserUpdateAdmin,
        current_user: User | None = None,
    ) -> User:
        """Обновляет пользователя (админ не может деактивировать себя)."""

        try:
            user_to_update = await self.get_object_or_404(user_id, session)
            update_data = request.model_dump(exclude_unset=True)
            if request.password is not None:
                update_data = self._add_password_hash(update_data)

            if isinstance(request, UserUpdateAdmin):
                self.validate_admin_self_update(
                    user_to_update, current_user, request
                )

            updated_user = await self.crud.update(
                user_to_update, update_data, session
            )
            logger.info(
                "Обновлен пользователь user_id={}",
                user_id,
            )
            return updated_user

        except IntegrityError as e:
            await session.rollback()
            self._handle_integrity_error(e, "update")

    def validate_admin_self_update(
        self,
        user_to_update: User,
        current_user: User,
        user_update_schema: UserUpdateAdmin,
    ) -> None:
        """Проверяет, что админ не пытается деактивировать сам себя."""

        if (
            user_to_update.id == current_user.id
            and user_update_schema.is_active is False
        ):
            logger.warning(
                "Админ user_id={} пытался деактивировать себя",
                current_user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=SELF_DEACTIVATE,
            )

    async def get_users(
        self,
        session: AsyncSession,
        **filters,
    ) -> list[User]:
        """Возвращает список пользователей с опциональной фильтрацией."""

        if filters:
            return await self.crud.get_multi(session, **filters)
        return await self.crud.get_multi(session)


user_service = UserService(user_crud)
