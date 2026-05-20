from typing import Any, Generic, Type

from fastapi import HTTPException, status
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import (
    CRUDType,
    CreateSchemaType,
    ModelType,
    UpdateSchemaType,
)


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
            if column is not None and column.comment:
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

        if "uq_service_master" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Услуга уже добавлена",
            )

        for field in cls._get_unique_fields():
            if field in error_msg:
                field_name = cls._get_field_name(field)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Поле '{field_name}' уже занято",
                )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Конфликт данных при сохранении",
        )

    async def get_object_or_404(
        self, obj_id: int, session: AsyncSession
    ) -> ModelType:
        obj = await self.crud.get(obj_id, session)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Объект не найден",
            )
        return obj

    async def create(
        self,
        request: CreateSchemaType | dict[str, Any],
        session: AsyncSession,
    ) -> ModelType:
        try:
            return await self.crud.create(request, session)

        except IntegrityError as e:
            await session.rollback()
            self._handle_integrity_error(e, "create")

    async def update(
        self,
        session: AsyncSession,
        obj_id: int,
        request: UpdateSchemaType,
        obj: ModelType | None = None,
    ) -> ModelType:
        try:
            if obj is None:
                obj = await self.get_object_or_404(obj_id, session)
            return await self.crud.update(obj, request, session)

        except IntegrityError as e:
            await session.rollback()
            self._handle_integrity_error(e, "update")
