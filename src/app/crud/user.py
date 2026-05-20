from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas import UserCreate, UserUpdateAdmin, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate | UserUpdateAdmin]):
    """CRUD для модели User."""


user_crud = CRUDUser(User)
