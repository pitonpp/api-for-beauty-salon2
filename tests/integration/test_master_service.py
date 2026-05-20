import pytest
from fastapi import HTTPException

from app.crud.user import user_crud
from app.crud.service import service_crud
from app.crud.master import master_crud
from app.schemas.status_enum import UserRole
from app.services.master import master_manager
from app.services.master_service import master_service_manager
from app.schemas.master import MasterAdminCreate
from app.schemas.master_service import MasterServiceCreate
from datetime import timedelta


class TestMasterIntegration:
    async def test_create_master_and_downgrade(self, session):
        user = await user_crud.create(
            {
                "phone": "+79234567890",
                "username": "new_master",
                "email": "master@test.com",
                "first_name": "Мастер",
                "password": "hash",
                "role": UserRole.USER,
                "is_active": True,
            },
            session,
        )

        request = MasterAdminCreate(user_id=user.id, experience=5)
        master = await master_manager.create_master(session, request)

        assert master.id is not None
        assert user.role == UserRole.MASTER

        # downgrade
        await master_manager.downgrade_role(session, user.id)
        assert user.role == UserRole.USER

    async def test_create_and_get_master_service(self, session):
        user = await user_crud.create(
            {
                "phone": "+79234567891",
                "username": "master_svc",
                "email": "svc@test.com",
                "first_name": "Сервис",
                "password": "hash",
                "role": UserRole.MASTER,
                "is_active": True,
            },
            session,
        )
        master = await master_crud.create(
            {"user_id": user.id, "bio": "Тест", "experience": 2},
            session,
        )
        svc = await service_crud.create({"name": "Маникюр"}, session)

        request = MasterServiceCreate(
            service_id=svc.id,
            price=2000.00,
            description="Маникюр классический",
            duration=timedelta(hours=1),
        )
        ms = await master_service_manager.create_master_service_admin(
            session, request, master_id=master.id,
        )

        assert ms.id is not None

        fetched = await master_service_manager.get_master_service(
            session, master_id=master.id, service_id=svc.id,
        )
        assert fetched.id == ms.id
