from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.app.crud.base import CRUDBase
from src.app.models.service import Service


class CRUDService(CRUDBase):
    async def get_service_id_by_name(
        self, name: str, session: AsyncSession
    ) -> Optional[int]:
        service_id = await session.execute(
            select(Service.id).where(Service.name == name)
        )
        service_id = service_id.scalar_one_or_none()
        return service_id


service_crud = CRUDService(Service)
