from fastapi import APIRouter

from app.api.dependencies import SessionDI, ValidClientDI, check_unique_phone

from app.crud.client import client_crud
from app.schemas.client import ClientUpdate, ClientCreate, ClientDB

router = APIRouter()


@router.get(
    "/", response_model=list[ClientDB], summary="Получить список клиентов"
)
async def get_all_clients(session: SessionDI):
    clients = await client_crud.get_multi(session)
    return clients


@router.post("/", response_model=ClientDB, summary="Создать нового клиента")
async def create_new_client(client: ClientCreate, session: SessionDI):
    await check_unique_phone(client.phone, session)
    new_client = await client_crud.create(client, session)
    return new_client


@router.patch(
    "/{client_id}", response_model=ClientDB, summary="Обновить данные клиента"
)
async def update_client(
    client: ValidClientDI, obj_in: ClientUpdate, session: SessionDI
):
    if obj_in.phone is not None:
        await check_unique_phone(obj_in.phone, session)

    client = await client_crud.update(client, obj_in, session)
    return client


@router.delete(
    "/{client_id}", response_model=ClientDB, summary="Удалить клиента"
)
async def delete_client(client: ValidClientDI, session: SessionDI):
    client = await client_crud.delete(client, session)
    return client
