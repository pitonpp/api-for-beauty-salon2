from typing import Generic, Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import Base
from app.crud.base import CRUDBase

CRUDType = TypeVar("CRUDType", bound=CRUDBase)
ModelType = TypeVar("ModelType", bound=Base)


class BaseService(Generic[ModelType, CRUDType]):
    model: Type[ModelType]
    custom_fields_names: dict[str, str] = {}

    def __init__(self, crud: CRUDType) -> None:
        self.crud = crud

    @classmethod
    def _get_field_name(cls, field: str) -> str:
        if field in cls.custom_fields_names:
            return cls.custom_fields_names[field]

        if cls.model:
            inspector = inspect(cls.model)
            column = inspector.columns.get(field)
            if column and column.comment:
                return column.comment

        return " ".join(word.capitalize() for word in field.split("_"))

    @classmethod
    def _get_unique_fields(cls) -> list[str]:
        if not cls.model:
            return []

        inspector = inspect(cls.model)
        return [column.name for column in inspector.columns if column.unique]

    @classmethod
    def _handle_integrity_error(
        cls, e: IntegrityError, operation: str
    ) -> None:
        error_msg = str(e.orig).lower()
        operation_name = {"create": "создании", "update": "обновлении"}.get(
            operation, operation
        )

        for field in cls._get_unique_fields():
            if field in error_msg:
                field_name = cls._get_field_name(field)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Поле {field_name} уже занято",
                )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Конфликт данных при сохранении",
        )

    async def validate_object_id(
        self, obj_id: int, session: AsyncSession
    ) -> ModelType:
        obj = await self.crud.get(obj_id, session)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Объект не найден",
            )
        return obj
