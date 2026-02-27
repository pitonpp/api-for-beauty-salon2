from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.client import Client


class CRUDClient(CRUDBase):
    async def get_by_phone(
        self, phone: str, session: AsyncSession
    ) -> Optional[Client]:
        client = await session.execute(
            select(Client).where(Client.phone == phone)
        )
        client = client.scalar_one_or_none()
        return client


client_crud = CRUDClient(Client)
