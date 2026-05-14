from typing import Annotated, Callable

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import JWT_USER_ID
from app.core.jwt_services import TokenService, token_service
from app.crud.user import CRUDUser, user_crud
from app.models.user import User
from app.schemas.status_enum import UserRole
from app.schemas.user import Token
from app.services.password import verify_password
from app.core.db import get_async_session

from .base import BaseService


SessionDependency = Annotated[AsyncSession, Depends(get_async_session)]


class AuthService(BaseService[User, CRUDUser]):
    model = User

    def __init__(
        self,
        user_crud: CRUDUser,
        token_service: TokenService,
    ) -> None:
        super().__init__(user_crud)
        self.token_service = token_service

    async def get_current_user(
        self,
        session: AsyncSession,
        token: str,
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

    def get_token_from_request(self, request: Request) -> str:
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            return auth[7:]
        token = self._get_token_from_cookie(request, True)
        if token:
            return token

    def role_check(self, *allowed_roles: UserRole) -> Callable[..., User]:

        async def checker(
            session: SessionDependency,
            request: Request,
            # token: str = Depends(oauth2_scheme),
        ) -> User:
            token = self.get_token_from_request(request)
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
        return self.role_check(
            UserRole.USER,
            UserRole.ADMIN,
            UserRole.MASTER,
        )

    def allow_admin_and_master(self) -> Callable[..., User]:
        return self.role_check(
            UserRole.ADMIN,
            UserRole.MASTER,
        )

    async def get_by_username(
        self, session: AsyncSession, username: str
    ) -> User | None:
        return await self.crud.get_one_by(session, username=username)

    async def login(
        self,
        session: AsyncSession,
        username: str,
        password: str,
        response: Response,
    ) -> Token:
        user = await self.get_by_username(session, username)

        if not user or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный логин или пароль",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Пользователь заблокирован",
            )

        access_token, refresh_token = await self.token_service.create_tokens(
            data={JWT_USER_ID: user.id},
            session=session,
        )
        response.set_cookie(
            "refresh_token",
            refresh_token,
            httponly=True,
        )
        response.set_cookie(
            "access_token",
            access_token,
            httponly=True,
            max_age=self.token_service.access_token_expire_minutes * 60,
        )
        return Token(access_token=access_token)

    async def logout(
        self, response: Response, refresh_token: str, session: AsyncSession
    ) -> None:
        token_data = await self.token_service.verify_refresh_token(
            refresh_token, session
        )
        response.delete_cookie("refresh_token")
        response.delete_cookie("access_token")
        await self.token_service.revoke_token(token_data, session)

    def _get_token_from_cookie(
        self,
        request: Request,
        is_acces_token: bool = False,
    ) -> str:
        if is_acces_token:
            token = request.cookies.get("access_token")
        else:
            token = request.cookies.get("refresh_token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен не найден",
            )
        return token

    def get_refresh_token_from_cookie(self, request: Request) -> str:
        return self._get_token_from_cookie(request)

    def get_access_token_from_cookie(self, request: Request) -> str:
        return self._get_token_from_cookie(request, True)

    async def refresh(
        self, session: AsyncSession, request: Request, response: Response
    ) -> Token:
        refresh_token = self.get_refresh_token_from_cookie(request)
        (
            new_access_token,
            new_refresh_token,
        ) = await self.token_service.refresh_tokens(refresh_token, session)
        response.set_cookie(
            "refresh_token",
            new_refresh_token,
            httponly=True,
        )
        response.set_cookie(
            "access_token",
            new_access_token,
            httponly=True,
            max_age=self.token_service.access_token_expire_minutes * 60,
        )
        return Token(access_token=new_access_token)


auth_service = AuthService(user_crud, token_service)
