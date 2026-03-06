from typing import Optional

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
import bcrypt

from app.crud.base import CRUDBase
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CRUDUser(CRUDBase):
    async def verify_password(
        self, plain_password: str, hashed_password: str
    ) -> bool:
        """Проверяет, совпадает ли пароль с хэшем"""
        # return pwd_context.verify(plain_password, hashed_password)
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    async def get_password_hash(self, password: str) -> str:
        """Хэширует пароль"""
        # return pwd_context.hash(password)
        return bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    async def get_by_phone(
        self,
        session: AsyncSession,
        phone: Optional[str] = None,
    ) -> Optional[User]:
        user = await session.execute(select(User).where(User.phone == phone))
        user = user.scalar_one_or_none()
        return user

    async def create_user(self, request, session: AsyncSession) -> User:
        request_data = request.model_dump()

        if request_data.get("password"):
            request_data["password"] = await self.get_password_hash(
                request_data["password"]
            )

        db_obj = User(**request_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update_user(
        self, db_obj, request, session: AsyncSession
    ) -> User:
        obj_data = jsonable_encoder(db_obj)
        update_data = request.model_dump(exclude_unset=True)

        if update_data.get("password"):
            update_data["password"] = await self.get_password_hash(
                update_data["password"]
            )

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj


user_crud = CRUDUser(User)
