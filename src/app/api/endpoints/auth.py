from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.user import Token
from ..dependencies import AuthServiceDI, SessionDI, AllowUserDI


router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    session: SessionDI,
    auth_service: AuthServiceDI,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    return await auth_service.login(
        session, form_data.username, form_data.password, response
    )


@router.post("/logout", response_description="Вы успешно вышли.")
async def logout(
    session: SessionDI,
    auth_service: AuthServiceDI,
    response: Response,
    request: Request,
    _: AllowUserDI,
) -> None:
    refresh_token = auth_service.get_refresh_token_from_cookie(request)
    await auth_service.logout(response, refresh_token, session)


@router.post("/refresh", response_model=Token)
async def refresh(
    session: SessionDI,
    auth_service: AuthServiceDI,
    response: Response,
    request: Request,
    _: AllowUserDI,
) -> Token:
    return await auth_service.refresh(session, request, response)
