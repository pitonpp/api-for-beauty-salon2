from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user import CRUDUser, user_crud
from app.models.user import User
from app.schemas import UserCreate, UserUpdate, UserUpdateAdmin

from .base import BaseService
from .password import hash_password


class UserService(BaseService[User, CRUDUser]):
    model = User

    def __init__(self, crud: CRUDUser) -> None:
        super().__init__(crud)

    def _add_password_hash(self, data: dict[str, Any]) -> dict[str, Any]:
        if "password" not in data or data["password"] is None:
            return data

        data = data.copy()
        data["password"] = hash_password(data["password"])
        return data

    async def create_user(
        self, session: AsyncSession, request: UserCreate
    ) -> User:
        try:
            request_data = request.model_dump()
            request_data = self._add_password_hash(request_data)

            return await self.crud.create(request_data, session)

        except IntegrityError as e:
            await session.rollback()
            self._handle_integrity_error(e, "create")

    async def update_user(
        self,
        user_id: int,
        session: AsyncSession,
        request: UserUpdate | UserUpdateAdmin,
        current_user: User,
    ) -> User:
        try:
            user_to_update = await self.validate_object_id(user_id, session)
            update_data = request.model_dump(exclude_unset=True)
            if request.password is not None:
                update_data = self._add_password_hash(update_data)

            if isinstance(request, UserUpdateAdmin):
                self.validate_admin_self_update(
                    user_to_update, current_user, request
                )

            return await self.crud.update(
                user_to_update, update_data, session
            )

        except IntegrityError as e:
            await session.rollback()
            self._handle_integrity_error(e, "update")

    def validate_admin_self_update(
        self,
        user_to_update: User,
        current_user: User,
        user_update_schema: UserUpdateAdmin,
    ) -> None:
        if (
            user_to_update.id == current_user.id
            and user_update_schema.is_active is False
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Админ не может деактивировать сам себя",
            )


user_service = UserService(user_crud)
