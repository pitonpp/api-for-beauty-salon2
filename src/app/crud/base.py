from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDBase:
    def __init__(self, model):
        self.model = model

    async def get(self, obj_id: int, session: AsyncSession):
        db_obj = await session.execute(
            select(self.model).where(self.model.id == obj_id)
        )
        return db_obj.scalar_one_or_none()

    async def get_multi(
        self, session: AsyncSession, skip: int = 0, limit: int = 10
    ):
        db_objs = await session.execute(
            select(self.model)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.id)
        )
        return db_objs.scalars().all()

    async def create(self, request, session: AsyncSession):
        request_data = request.model_dump()
        db_obj = self.model(**request_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(self, db_obj, request, session: AsyncSession):
        obj_data = jsonable_encoder(db_obj)
        update_data = request.model_dump(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj, session: AsyncSession):
        await session.delete(db_obj)
        await session.commit()
        return db_obj
