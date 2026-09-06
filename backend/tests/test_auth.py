import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    payload = {
        "email": "farmer1@livestockos.io",
        "password": "strongpassword123",
        "full_name": "Suresh Reddy",
        "phone_number": "9123456780",
        "farm_name": "Reddy Cattle Ranch",
        "village": "Kondapur",
        "district": "Rangareddy",
        "state": "Telangana"
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "farmer1@livestockos.io"
    assert data["full_name"] == "Suresh Reddy"
    assert data["role"] == "FARMER"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {
        "email": "duplicate@livestockos.io",
        "password": "password123",
        "full_name": "Farmer Duplicate"
    }
    res1 = await client.post("/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await client.post("/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["message"].lower()


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    payload = {
        "email": "testfarmer@livestockos.io",
        "password": "password123"
    }
    response = await client.post("/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, test_user):
    payload = {
        "email": "testfarmer@livestockos.io",
        "password": "wrongpassword"
    }
    response = await client.post("/auth/login", json=payload)
    assert response.status_code == 401
    assert "incorrect" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_email(client: AsyncClient):
    payload = {
        "email": "nonexistent@livestockos.io",
        "password": "password123"
    }
    response = await client.post("/auth/login", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_headers):
    response = await client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testfarmer@livestockos.io"
    assert data["full_name"] == "Test Farmer"
    assert data["farm_name"] == "Green Valley Test Farm"


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, test_user):
    login_res = await client.post(
        "/auth/login",
        json={"email": "testfarmer@livestockos.io", "password": "password123"}
    )
    refresh_token = login_res.json()["refresh_token"]

    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, auth_headers):
    response = await client.post("/auth/logout", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True

    # After logout, accessing protected route with the same token should be rejected
    me_res = await client.get("/auth/me", headers=auth_headers)
    assert me_res.status_code == 401
