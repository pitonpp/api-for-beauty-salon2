from typing import Any, Generic, Type

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import (
    CONFLICT_SAVING,
    OBJECT_NOT_FOUND,
    SERVICE_ALREADY_ADDED,
)
from app.core.types import (
    CRUDType,
    CreateSchemaType,
    ModelType,
    UpdateSchemaType,
)


class BaseService(Generic[ModelType, CRUDType]):
    """Базовый сервис с бизнес-логикой для CRUD-операций."""

    model: Type[ModelType]
    custom_fields_names: dict[str, str] = {}

    def __init__(self, crud: CRUDType) -> None:
        """Инициализирует базовый сервис с CRUD-объектом."""
        self.crud = crud

    @classmethod
    def _get_field_name(cls, field: str) -> str:
        """Возвращает имя поля (из comment или кастомного словаря)."""
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
        """Возвращает список уникальных полей модели."""
        if not cls.model:
            return []

        inspector = inspect(cls.model)
        return [column.name for column in inspector.columns if column.unique]

    @classmethod
    def _handle_integrity_error(
        cls, e: IntegrityError, operation: str,
    ) -> None:
        """Обрабатывает IntegrityError с понятным сообщением об ошибке."""
        error_msg = str(e.orig).lower()

        if "uq_service_master" in error_msg:
            logger.warning("Попытка добавить уже созданную услугу")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=SERVICE_ALREADY_ADDED,
            )

        for field in cls._get_unique_fields():
            if field in error_msg:
                field_name = cls._get_field_name(field)
                logger.warning(
                    "Ошибка при добавлении: поле '{}' уже занято",
                    field_name,
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Поле '{field_name}' уже занято",
                )

        logger.opt(exception=True).warning("Ошибка целостности: {}", e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=CONFLICT_SAVING,
        )

    async def get_object_or_404(
        self, obj_id: int, session: AsyncSession,
    ) -> ModelType:
        """Возвращает объект или выбрасывает 404."""
        obj = await self.crud.get(obj_id, session)
        if not obj:
            logger.warning(
                "{} id={} не найден",
                self.model.__name__,
                obj_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=OBJECT_NOT_FOUND,
            )
        return obj

    async def create(
        self,
        request: CreateSchemaType | dict[str, Any],
        session: AsyncSession,
    ) -> ModelType:
        """Создаёт объект с обработкой IntegrityError."""
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
        """Обновляет объект по ID или переданному объекту."""
        try:
            if obj is None:
                obj = await self.get_object_or_404(obj_id, session)
            return await self.crud.update(obj, request, session)

        except IntegrityError as e:
            await session.rollback()
            self._handle_integrity_error(e, "update")
