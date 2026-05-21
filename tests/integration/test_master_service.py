from datetime import timedelta

import pytest
from fastapi import HTTPException

from app.crud.service import service_crud
from app.schemas.master import MasterAdminCreate
from app.schemas.master_service import MasterServiceCreate
from app.schemas.status_enum import UserRole
from app.services.master import master_manager
from app.services.master_service import master_service_manager
from tests.integration.factories import make_master, make_user


@pytest.mark.integration
class TestMasterIntegration:
    async def test_create_master_and_downgrade(self, session):
        user = await make_user(
            session,
            username='new_master',
            email='master@test.com',
            role=UserRole.USER,
            phone='+79234567890',
        )

        request = MasterAdminCreate(user_id=user.id, experience=5)
        master = await master_manager.create_master(session, request)

        assert master.id is not None
        assert user.role == UserRole.MASTER

        await master_manager.downgrade_role(session, user.id)
        assert user.role == UserRole.USER

    async def test_create_and_get_master_service(self, session):
        user = await make_user(
            session,
            username='master_svc',
            email='svc@test.com',
            role=UserRole.MASTER,
            phone='+79234567891',
        )
        master = await make_master(session, user=user)
        svc = await service_crud.create({'name': 'Маникюр'}, session)

        request = MasterServiceCreate(
            service_id=svc.id,
            price=2000.00,
            description='Маникюр классический',
            duration=timedelta(hours=1),
        )
        ms = await master_service_manager.create_master_service_admin(
            session,
            request,
            master_id=master.id,
        )

        assert ms.id is not None

        fetched = await master_service_manager.get_master_service(
            session,
            master_id=master.id,
            service_id=svc.id,
        )
        assert fetched.id == ms.id

    async def test_downgrade_nonexistent_user_raises_404(self, session):
        with pytest.raises(HTTPException) as exc:
            await master_manager.downgrade_role(session, 99999)
        assert exc.value.status_code == 404

    async def test_create_master_for_nonexistent_user_raises_404(
        self,
        session,
    ):
        request = MasterAdminCreate(user_id=99999, experience=5)
        with pytest.raises(HTTPException) as exc:
            await master_manager.create_master(session, request)
        assert exc.value.status_code == 404
