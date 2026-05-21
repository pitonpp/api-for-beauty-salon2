from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from itertools import count

from app.crud.master import master_crud
from app.crud.master_service import master_service_crud
from app.crud.service import service_crud
from app.crud.user import user_crud
from app.models.master import Master
from app.models.master_service import MasterService
from app.models.service import Service
from app.models.user import User
from app.schemas.status_enum import UserRole

_counter = count(1)


def _uniq(tag: str) -> str:
    return f'{tag}_{next(_counter)}'


async def make_user(
    session,
    *,
    role: UserRole = UserRole.USER,
    is_active: bool = True,
    **overrides,
) -> User:
    tag = _uniq('user')
    data = {
        'phone': overrides.pop('phone', f'+79{next(_counter):09d}'),
        'username': overrides.pop('username', tag),
        'email': overrides.pop('email', f'{tag}@test.com'),
        'first_name': overrides.pop('first_name', tag),
        'last_name': overrides.pop('last_name', None),
        'password': overrides.pop('password', 'hashed_secret'),
        'role': role,
        'is_active': is_active,
    }
    data.update(overrides)
    return await user_crud.create(data, session)


async def make_service(session, **overrides) -> Service:
    tag = _uniq('svc')
    data = {
        'name': overrides.pop('name', tag),
        'is_active': overrides.pop('is_active', True),
    }
    data.update(overrides)
    return await service_crud.create(data, session)


async def make_master(
    session,
    *,
    user: User | None = None,
    **overrides,
) -> Master:
    if user is None:
        user = await make_user(session, role=UserRole.MASTER)
    data = {
        'user_id': user.id,
        'bio': overrides.pop('bio', 'Мастер'),
        'experience': overrides.pop('experience', 3),
    }
    data.update(overrides)
    return await master_crud.create(data, session)


async def make_master_service(
    session,
    *,
    master: Master | None = None,
    service: Service | None = None,
    **overrides,
) -> MasterService:
    if master is None:
        master = await make_master(session)
    if service is None:
        service = await make_service(session)
    data = {
        'master_id': master.id,
        'service_id': service.id,
        'price': overrides.pop('price', 1500.00),
        'description': overrides.pop('description', 'Услуга'),
        'duration': overrides.pop('duration', timedelta(hours=1)),
    }
    data.update(overrides)
    return await master_service_crud.create(data, session)


@asynccontextmanager
async def seeded_appointment(session) -> AsyncIterator[dict]:
    user = await make_user(session)
    svc = await make_service(session)
    master = await make_master(
        session,
        user=await make_user(session, role=UserRole.MASTER),
    )
    ms = await make_master_service(session, master=master, service=svc)
    yield {
        'user': user,
        'service': svc,
        'master': master,
        'master_service': ms,
    }
