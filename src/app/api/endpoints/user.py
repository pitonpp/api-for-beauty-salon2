from fastapi import APIRouter

from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserDB,
    UserShort,
    UserUpdate,
    UserUpdateAdmin,
)

from ..dependencies import (
    AllowAdminDI,
    AllowUserDI,
    SessionDI,
    UserServiceDI,
)

router = APIRouter()


@router.post("/sign_up", response_model=UserShort)
async def sign_up(
    session: SessionDI, request: UserCreate, user_service: UserServiceDI
):
    return await user_service.create_user(session, request)


@router.get("/me", response_model=UserDB)
async def get_me(
    session: SessionDI,
    user: AllowUserDI,
) -> User:
    return user


@router.patch("/me", response_model=UserDB)
async def update_me(
    session: SessionDI,
    user: AllowUserDI,
    request: UserUpdate,
    user_service: UserServiceDI,
) -> User:
    return await user_service.update_user(user.id, session, request)


@router.patch("/{user_id}", response_model=UserDB)
async def update_user(
    session: SessionDI,
    request: UserUpdateAdmin,
    user_service: UserServiceDI,
    user: AllowAdminDI,
    user_id: int,
) -> User:
    return await user_service.update_user(user_id, session, request, user)


@router.get("/", response_model=list[UserDB])
async def get_users(
    session: SessionDI, _: AllowAdminDI, user_service: UserServiceDI
) -> list[User]:
    return await user_service.get_multi(session)


@router.get("/{user_id}", response_model=UserDB)
async def get_user(
    session: SessionDI,
    user_id: int,
    user_service: UserServiceDI,
    _: AllowAdminDI,
) -> User:
    return await user_service.validate_object_id(user_id, session)
