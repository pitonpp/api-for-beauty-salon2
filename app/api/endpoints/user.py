from fastapi import APIRouter

from app.api.dependencies import (
    SessionDI,
    check_unique_phone,
    valid_client_id,
)
from app.crud.user import user_crud
from app.schemas.user import UserCreate, UserDB, UserUpdate

router = APIRouter()


@router.get(
    "/", response_model=list[UserDB], summary="Получить список клиентов"
)
async def get_all_clients(session: SessionDI):
    users = await user_crud.get_multi(session)
    return users


@router.post("/", response_model=UserDB, summary="Создать нового клиента")
async def create_new_client(client: UserCreate, session: SessionDI):
    await check_unique_phone(client.phone, session)
    new_user = await user_crud.create(client, session)
    return new_user


@router.patch(
    "/{user_id}", response_model=UserDB, summary="Обновить данные клиента"
)
async def update_client(user_id: int, obj_in: UserUpdate, session: SessionDI):
    user = await valid_client_id(user_id, session)

    if obj_in.phone is not None:
        await check_unique_phone(obj_in.phone, session)

    user = await user_crud.update(user, obj_in, session)
    return user


@router.delete("/{user_id}", response_model=UserDB, summary="Удалить клиента")
async def delete_client(user_id: int, session: SessionDI):
    user = await valid_client_id(user_id, session)
    user = await user_crud.delete(user, session)
    return user
