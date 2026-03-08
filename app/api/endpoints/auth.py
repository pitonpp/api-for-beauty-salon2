from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import (
    SessionDI,
    check_unique_phone,
    get_current_user,
    role_checker,
    valid_user_id,
)
from app.core.jwt_services import create_access_token
from app.crud.user import user_crud
from app.models.user import User
from app.schemas.status_enum import UserRole
from app.schemas.user import Token, UserCreate, UserDB, UserShort, UserUpdate

router = APIRouter()


@router.post(
    "/signup",
    response_model=UserShort,
    summary="Создать нового пользователя",
    status_code=201,
)
async def create_user(user: UserCreate, session: SessionDI):
    await check_unique_phone(user.phone, session)
    new_user = await user_crud.create_user(user, session)
    return new_user


@router.get(
    "/me",
    response_model=UserDB,
    summary="Получить информацию о текущем пользователе",
)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post(
    "/login", response_model=Token, summary="Авторизация пользователя"
)
async def login(
    session: SessionDI, form_data: OAuth2PasswordRequestForm = Depends()
):
    user = await user_crud.get_by_phone(session, form_data.username)
    if user is None or not await user_crud.verify_password(
        form_data.password, user.password
    ):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )
    access_token = create_access_token(data={"user_id": str(user.id)})
    return Token(access_token=access_token)


@router.get(
    "/users",
    response_model=list[UserDB],
    summary="Получить список пользователей",
    dependencies=[Depends(role_checker(UserRole.ADMIN))],
)
async def get_users(session: SessionDI):
    """Только для админа"""
    users = await user_crud.get_multi(session)
    return users


# Здесь надо будет переписать ручку,
# чтобы через /me обновлять текущего пользователя
# или оставить эту для админа
@router.patch(
    "/{user_id}",
    response_model=UserDB,
    summary="Обновить данные пользователя",
)
async def update_client(user_id: int, obj_in: UserUpdate, session: SessionDI):
    user = await valid_user_id(user_id, session)

    if obj_in.phone is not None:
        await check_unique_phone(obj_in.phone, session)

    user = await user_crud.update(user, obj_in, session)
    return user


@router.delete(
    "/{user_id}",
    response_model=UserDB,
    summary="Удалить пользователя",
    dependencies=[Depends(role_checker(UserRole.ADMIN))],
)
async def delete_client(
    user_id: int,
    session: SessionDI,
):
    """Только для админа"""
    user = await valid_user_id(user_id, session)
    user = await user_crud.delete(user, session)
    return user
