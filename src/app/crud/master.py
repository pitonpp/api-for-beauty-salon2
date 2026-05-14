from app.crud.base import CRUDBase
from app.models.master import Master
from app.schemas.master import MasterAdminCreate, MasterAdminUpdate


class CRUDMaster(CRUDBase[Master, MasterAdminCreate, MasterAdminUpdate]):
    pass


master_crud = CRUDMaster(Master)


master_crud = CRUDMaster(Master)
