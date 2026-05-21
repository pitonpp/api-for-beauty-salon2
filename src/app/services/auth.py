from typing import Annotated, Callable

from fastapi import Depends, HTTPException, Request, Response, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import (
    ACCESS_TOKEN_COOKIE,
    AUTHORIZATION_HEADER,
    BEARER_PREFIX,
    INVALID_CREDENTIALS,
    JWT_USER_ID,
    MISSING_TOKEN,
    NO_PERMISSION,
    REFRESH_TOKEN_COOKIE,
    TOKEN_NOT_FOUND,
    USER_BLOCKED,
    USER_NOT_FOUND,
)
from app.core.db import get_async_session
from app.core.jwt_services import TokenService, token_service
from app.crud.user import CRUDUser, user_crud
from app.models.user import User
from app.schemas.status_enum import UserRole
from app.schemas.user import Token
from app.services.password import verify_password

from .base import BaseService

SessionDependency = Annotated[AsyncSession, Depends(get_async_session)]


class AuthService(BaseService[User, CRUDUser]):
    """Сервис аутентификации: логин, логаут, refresh, проверка ролей."""

    model = User

    def __init__(
        self,
        user_crud: CRUDUser,
        token_service: TokenService,
    ) -> None:
        """Инициализирует сервис аутентификации."""
        super().__init__(user_crud)
        self.token_service = token_service

    async def get_current_user(
        self,
        session: AsyncSession,
        token: str,
    ) -> User:
        """Возвращает текущего пользователя по access-токену."""
        token_data = self.token_service.verify_access_token(token)
        user = await self.crud.get(token_data.user_id, session)

        if not user:
            logger.warning(
                'Пользователь user_id={} из токена не найден в БД',
                token_data.user_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=USER_NOT_FOUND,
            )

        if not user.is_active:
            logger.warning(
                'Пользователь user_id={} заблокирован',
                token_data.user_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=USER_BLOCKED,
            )

        return user

    def get_token_from_request(self, request: Request) -> str:
        """Извлекает токен из заголовка Authorization или cookie."""
        auth = request.headers.get(AUTHORIZATION_HEADER)
        if auth and auth.startswith(BEARER_PREFIX):
            return auth[len(BEARER_PREFIX) :]

        token = self._get_token_from_cookie(request, True)
        if token:
            return token

        logger.warning('Токен не найден: path={}', request.url.path)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=MISSING_TOKEN,
        )

    def role_check(self, *allowed_roles: UserRole) -> Callable[..., User]:
        """Возвращает dependency для проверки разрешённой роли."""

        async def checker(
            session: SessionDependency,
            request: Request,
            # token: str = Depends(oauth2_scheme),
        ) -> User:
            token = self.get_token_from_request(request)
            user = await self.get_current_user(session, token)

            if user.role not in allowed_roles:
                logger.warning(
                    'Пользователь user_id={} role={} не имеет прав',
                    user.id,
                    user.role,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=NO_PERMISSION,
                )
            return user

        return checker

    def allow_admin_only(self) -> Callable[..., User]:
        """Только для администраторов."""
        return self.role_check(UserRole.ADMIN)

    def allow_users(self) -> Callable[..., User]:
        """Для всех аутентифицированных пользователей."""
        return self.role_check(
            UserRole.USER,
            UserRole.ADMIN,
            UserRole.MASTER,
        )

    def allow_admin_and_master(self) -> Callable[..., User]:
        """Для администраторов и мастеров."""
        return self.role_check(
            UserRole.ADMIN,
            UserRole.MASTER,
        )

    async def get_by_username(
        self,
        session: AsyncSession,
        username: str,
    ) -> User | None:
        """Возвращает пользователя по username."""
        return await self.crud.get_one_by(session, username=username)

    async def login(
        self,
        session: AsyncSession,
        username: str,
        password: str,
        response: Response,
    ) -> Token:
        """Аутентифицирует пользователя и устанавливает токены в cookie."""
        user = await self.get_by_username(session, username)

        if not user or not verify_password(password, user.password):
            logger.warning('Неудачная попытка входа: username={}', username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_CREDENTIALS,
            )

        if not user.is_active:
            logger.warning(
                'Пользователь user_id={} заблокирован, попытка входа',
                user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=USER_BLOCKED,
            )

        access_token, refresh_token = await self.token_service.create_tokens(
            data={JWT_USER_ID: user.id},
            session=session,
        )
        response.set_cookie(
            REFRESH_TOKEN_COOKIE,
            refresh_token,
            httponly=True,
        )
        response.set_cookie(
            ACCESS_TOKEN_COOKIE,
            access_token,
            httponly=True,
            max_age=self.token_service.access_token_expire_minutes * 60,
        )
        logger.info(
            'Пользователь user_id={} username={} вошел в систему',
            user.id,
            user.username,
        )
        return Token(access_token=access_token)

    async def logout(
        self,
        response: Response,
        refresh_token: str,
        session: AsyncSession,
    ) -> None:
        """Удаляет токены из cookie и отзывает refresh-токен."""
        token_data = await self.token_service.verify_refresh_token(
            refresh_token,
            session,
        )
        response.delete_cookie(REFRESH_TOKEN_COOKIE)
        response.delete_cookie(ACCESS_TOKEN_COOKIE)
        await self.token_service.revoke_token(token_data, session)
        logger.info(
            'Пользователь user_id={} вышел из системы',
            token_data.user_id,
        )

    def _get_token_from_cookie(
        self,
        request: Request,
        is_acces_token: bool = False,
    ) -> str:
        """Извлекает access или refresh токен из cookie."""
        cookie_name = (
            ACCESS_TOKEN_COOKIE if is_acces_token else REFRESH_TOKEN_COOKIE
        )
        token = request.cookies.get(cookie_name)
        if not token:
            logger.warning(
                "Токен '{}' отсутствует в cookies",
                cookie_name,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=TOKEN_NOT_FOUND,
            )
        return token

    def get_refresh_token_from_cookie(self, request: Request) -> str:
        """Возвращает refresh-токен из cookie."""
        return self._get_token_from_cookie(request)

    def get_access_token_from_cookie(self, request: Request) -> str:
        """Возвращает access-токен из cookie."""
        return self._get_token_from_cookie(request, True)

    async def refresh(
        self,
        session: AsyncSession,
        request: Request,
        response: Response,
    ) -> Token:
        """Обновляет пару токенов по refresh-токену из cookie."""
        refresh_token = self.get_refresh_token_from_cookie(request)
        (
            new_access_token,
            new_refresh_token,
        ) = await self.token_service.refresh_tokens(refresh_token, session)
        response.set_cookie(
            REFRESH_TOKEN_COOKIE,
            new_refresh_token,
            httponly=True,
        )
        response.set_cookie(
            ACCESS_TOKEN_COOKIE,
            new_access_token,
            httponly=True,
            max_age=self.token_service.access_token_expire_minutes * 60,
        )
        logger.info('Токены обновлены')
        return Token(access_token=new_access_token)


auth_service = AuthService(user_crud, token_service)
