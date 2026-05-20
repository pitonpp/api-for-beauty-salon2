import pytest
from app.services.user import UserService, user_service


@pytest.fixture
def user_service_() -> UserService:
    return user_service
