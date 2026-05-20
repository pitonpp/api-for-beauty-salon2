from app.crud.base import CRUDBase
from app.models.service import Service
from app.schemas import ServiceCreate, ServiceUpdate


class CRUDService(CRUDBase[Service, ServiceCreate, ServiceUpdate]):
    """CRUD для модели Service."""


service_crud = CRUDService(Service)
