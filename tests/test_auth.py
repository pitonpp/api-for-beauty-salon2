import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/auth/signup",
        json={
            "name": "test_user",
            "phone": "+79999999999",
            "password": "test_password",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test_user"
    assert data["phone"] == "+79999999999"


@pytest.mark.asyncio
async def test_register_user_duplicate_phone(client: AsyncClient, user):
    response = await client.post(
        "/auth/signup",
        json={
            "name": "test_user",
            "phone": "+71234567890",
            "password": "test_password",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "уже существует" in data["detail"].lower()


@pytest.mark.asyncio
async def test_login(client: AsyncClient, user):
    response = await client.post(
        "/auth/login",
        data={
            "username": "+71234567890",
            "password": "test_password",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
