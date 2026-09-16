import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    """Test successful user registration."""
    payload = {
        "email": "testuser@example.com",
        "password": "SecurePassword123"
    }
    response = await client.post("/api/auth/register", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == payload["email"]
    assert "id" in data
    assert "hashed_password" not in data

@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client: AsyncClient):
    """Test registering with an already existing email returns HTTP 400."""
    payload = {
        "email": "duplicate@example.com",
        "password": "SecurePassword123"
    }
    resp1 = await client.post("/api/auth/register", json=payload)
    assert resp1.status_code == status.HTTP_201_CREATED

    resp2 = await client.post("/api/auth/register", json=payload)
    assert resp2.status_code == status.HTTP_400_BAD_REQUEST
    assert resp2.json()["message"] == "A user with this email already exists."

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test authenticating with valid credentials returns a Bearer token."""
    email = "login_test@example.com"
    password = "MyPassword123"
    await client.post("/api/auth/register", json={"email": email, "password": password})

    login_payload = {
        "username": email,
        "password": password
    }
    response = await client.post("/api/auth/login", data=login_payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_password_fails(client: AsyncClient):
    """Test authenticating with an incorrect password returns HTTP 401."""
    email = "wrong_pass@example.com"
    await client.post("/api/auth/register", json={"email": email, "password": "CorrectPassword123"})

    login_payload = {
        "username": email,
        "password": "WrongPassword123"
    }
    response = await client.post("/api/auth/login", data=login_payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["message"] == "Incorrect email or password"

@pytest.mark.asyncio
async def test_get_current_user_me_success(client: AsyncClient):
    """Test accessing /auth/me with a valid JWT token."""
    email = "me_user@example.com"
    password = "SecurePassword123"
    await client.post("/api/auth/register", json={"email": email, "password": password})

    login_response = await client.post(
        "/api/auth/login",
        data={"username": email, "password": password}
    )
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_response = await client.get("/api/auth/me", headers=headers)

    assert me_response.status_code == status.HTTP_200_OK
    data = me_response.json()
    assert data["email"] == email

@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient):
    """Test accessing /auth/me without a token returns HTTP 401."""
    response = await client.get("/api/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED