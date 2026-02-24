from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.service import Service


class CRUDService(CRUDBase):
    pass


service = CRUDService(Service)
