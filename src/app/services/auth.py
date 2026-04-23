from typing import Callable

from core.jwt_services import TokenService, token_service
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user import CRUDUser, user_crud
from app.models.user import User
from app.schemas.status_enum import UserRole

from .base import BaseService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class AuthService(BaseService[User, CRUDUser]):
    model = User

    def __init__(
        self, user_crud: CRUDUser, token_service: TokenService
    ) -> None:
        super().__init__(user_crud)
        self.token_service = token_service

    async def get_current_user(
        self, session: AsyncSession, token: str
    ) -> User:
        token_data = self.token_service.verify_access_token(token)
        user = await self.crud.get(token_data.user_id, session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Пользователь заблокирован",
            )

        return user

    def role_check(self, *allowed_roles: UserRole) -> Callable[..., User]:

        async def checker(
            session: AsyncSession, token: str = Depends(oauth2_scheme)
        ) -> User:
            user = await self.get_current_user(session, token)
            if user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="У вас нет прав для выполнения этого действия",
                )
            return user

        return checker

    def allow_admin_only(self) -> Callable[..., User]:
        return self.role_check(UserRole.ADMIN)

    def allow_users(self) -> Callable[..., User]:
        return self.role_check(UserRole.USER)


auth_service = AuthService(user_crud, token_service)
