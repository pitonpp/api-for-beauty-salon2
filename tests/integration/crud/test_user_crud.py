import pytest
from sqlalchemy.exc import IntegrityError

from app.crud.user import user_crud
from app.schemas.status_enum import UserRole
from tests.integration.factories import make_user


@pytest.mark.integration
class TestCRUDUser:
    async def test_create_user(
        self,
        session,
    ):
        user = await make_user(
            session,
            username='ivanov',
            email='ivanov@test.com',
            first_name='Иван',
            last_name='Иванов',
        )

        assert user.id is not None
        assert user.username == 'ivanov'
        assert user.email == 'ivanov@test.com'
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.password == 'hashed_secret'
        assert user.created_at is not None

    async def test_get_user_by_id(self, session):
        created = await make_user(session, username='petrov')
        fetched = await user_crud.get(created.id, session)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.username == 'petrov'

    async def test_get_user_by_username(self, session):
        await make_user(session, username='sidorov')
        fetched = await user_crud.get_one_by(session, username='sidorov')

        assert fetched is not None
        assert fetched.username == 'sidorov'

    async def test_get_user_not_found(self, session):
        fetched = await user_crud.get(99999, session)
        assert fetched is None

    async def test_get_user_by_nonexistent_username(self, session):
        fetched = await user_crud.get_one_by(session, username='nobody')
        assert fetched is None

    async def test_update_user(self, session):
        user = await make_user(session, username='update_me')
        updated = await user_crud.update(
            user,
            {'first_name': 'Обновлен', 'last_name': 'Обновленко'},
            session,
        )

        assert updated.first_name == 'Обновлен'
        assert updated.last_name == 'Обновленко'
        assert updated.username == 'update_me'

    async def test_duplicate_username_raises_integrity_error(
        self,
        session,
    ):
        await make_user(
            session,
            username='unique_user',
            email='first@test.com',
            phone='+79111111111',
        )
        with pytest.raises(IntegrityError):
            await make_user(
                session,
                username='unique_user',
                email='second@test.com',
                phone='+79222222222',
            )

    async def test_duplicate_email_raises_integrity_error(
        self,
        session,
    ):
        await make_user(
            session,
            username='user_one',
            email='dup@test.com',
            phone='+79111111111',
        )
        with pytest.raises(IntegrityError):
            await make_user(
                session,
                username='user_two',
                email='dup@test.com',
                phone='+79222222222',
            )

    async def test_duplicate_phone_raises_integrity_error(
        self,
        session,
    ):
        await make_user(
            session,
            username='user_one',
            email='one@test.com',
            phone='+79998887766',
        )
        with pytest.raises(IntegrityError):
            await make_user(
                session,
                username='user_two',
                email='two@test.com',
                phone='+79998887766',
            )

    async def test_delete_user(
        self,
        session,
    ):
        user = await make_user(session, username='to_delete')
        user_id = user.id

        deleted = await user_crud.delete(user, session)
        assert deleted.id == user_id

        fetched = await user_crud.get(user_id, session)
        assert fetched is None

    async def test_get_multi_users(
        self,
        session,
    ):
        await make_user(session, username='mu1')
        await make_user(session, username='mu2')
        await make_user(session, username='mu3')

        users = await user_crud.get_multi(session, skip=0, limit=10)
        assert len(users) >= 3
