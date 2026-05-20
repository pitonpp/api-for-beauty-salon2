from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.core.db import Base
    from app.crud.base import CRUDBase
    from app.services.base import BaseService

ModelType = TypeVar("ModelType", bound="Base")
CRUDType = TypeVar("CRUDType", bound="CRUDBase")
ManagerType = TypeVar("ManagerType", bound="BaseService")
SchemaType = TypeVar("SchemaType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
