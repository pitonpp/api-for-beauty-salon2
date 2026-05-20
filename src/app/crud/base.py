from typing import Any, Generic, Type

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import CreateSchemaType, ModelType, UpdateSchemaType


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(
        self,
        obj_id: int,
        session: AsyncSession,
    ) -> ModelType | None:
        return await session.get(self.model, obj_id)

    async def get_one_by(
        self,
        session: AsyncSession,
        **kwargs,
    ) -> ModelType | None:
        stmt = select(self.model).filter_by(**kwargs)
        db_obj = await session.execute(stmt)
        return db_obj.scalar_one_or_none()

    async def get_multi(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 10,
        **filters,
    ) -> list[ModelType]:
        stmt = select(self.model)

        if filters:
            stmt = stmt.filter_by(**filters)

        stmt = stmt.offset(skip).limit(limit).order_by(self.model.id)

        db_objs = await session.execute(stmt)
        return db_objs.scalars().all()

    async def create(
        self,
        request: CreateSchemaType | dict[str, Any],
        session: AsyncSession,
    ) -> ModelType:
        if isinstance(request, dict):
            request_data = request
        else:
            request_data = request.model_dump()

        db_obj = self.model(**request_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: ModelType,
        request: UpdateSchemaType | dict[str, Any],
        session: AsyncSession,
    ) -> ModelType:
        if isinstance(request, dict):
            update_data = request
        else:
            update_data = request.model_dump(exclude_unset=True)

        obj_data = jsonable_encoder(db_obj)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def delete(
        self, db_obj: ModelType, session: AsyncSession
    ) -> ModelType:
        await session.delete(db_obj)
        await session.commit()
        return db_obj
