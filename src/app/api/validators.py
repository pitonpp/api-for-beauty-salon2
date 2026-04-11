# from http import HTTPStatus

# from sqlalchemy.ext.asyncio import AsyncSession
# from fastapi import HTTPException

# from app.crud.client import client_crud
# from app.models.client import Client


# async def check_phone_duplicate(phone: str, session: AsyncSession) -> None:
#     client_id = await client_crud.get_client_id_by_phone(phone, session)
#     if client_id is not None:
#         raise HTTPException(
#             status_code=HTTPStatus.BAD_REQUEST,
#             detail="Телефон уже существует",
#         )


# async def check_client_exists(
#     client_id: int, session: AsyncSession
# ) -> Client:
#     client = await client_crud.get(client_id, session)
#     if client is None:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND, detail="Клиент не найден"
#         )
#     return client
