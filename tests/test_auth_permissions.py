import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import User


ME_ENDPOINT = "/api/auth/me"

@pytest_asyncio.fixture
async def active_user(db_session: AsyncSession) -> User:
    """Creates a regular active user."""
    user = User(
        email="standard@example.com",
        hashed_password=get_password_hash("Password123"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def inactive_user(db_session: AsyncSession) -> User:
    """Creates an inactive user."""
    user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("Password123"),
        is_active=False,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def superuser(db_session: AsyncSession) -> User:
    """Creates an active superuser."""
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("Password123"),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def get_auth_headers(user: User) -> dict[str, str]:
    """Generates Authorization headers containing a valid JWT for the user."""
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# TESTS: PROTECTED & UNAUTHENTICATED ACCESS
# ============================================================================

@pytest.mark.asyncio
async def test_protected_endpoint_rejects_unauthenticated(client: AsyncClient):
    """Requests without a token to /api/auth/me return 401 Unauthorized."""
    response = await client.get(ME_ENDPOINT)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_allows_active_user(
    client: AsyncClient, active_user: User
):
    """Authenticated active users should receive 200 OK and user data."""
    headers = get_auth_headers(active_user)
    response = await client.get(ME_ENDPOINT, headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == active_user.email


# ============================================================================
# TESTS: ACTIVE VS INACTIVE USER CHECKS
# ============================================================================

@pytest.mark.asyncio
async def test_inactive_user_is_blocked(client: AsyncClient, inactive_user: User):
    """Inactive users attempting to call /api/auth/me should be blocked (400 or 400/403)."""
    headers = get_auth_headers(inactive_user)
    response = await client.get(ME_ENDPOINT, headers=headers)
    assert response.status_code in (400, 403)


# ============================================================================
# TESTS: SUPERUSER PERMISSIONS
# ============================================================================

@pytest.mark.asyncio
async def test_superuser_can_access_protected_route(
    client: AsyncClient, superuser: User
):
    """Superusers can successfully access protected endpoints."""
    headers = get_auth_headers(superuser)
    response = await client.get(ME_ENDPOINT, headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == superuser.email