from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas import UserCreate, UserUpdateAdmin, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate | UserUpdateAdmin]):
    pass


user_crud = CRUDUser(User)
