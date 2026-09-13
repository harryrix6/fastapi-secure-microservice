import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_rate_limiter_allows_under_limit(client: AsyncClient):
    """Ensure requests under the rate limit succeed normally."""
    response = await client.get("/api/auth/me")  # Or any standard endpoint
    # Should fail with 401 Unauthorized (if unauthenticated), not 429 Rate Limited
    assert response.status_code != 429

@pytest.mark.asyncio
async def test_rate_limiter_blocks_exceeding_requests(client: AsyncClient):
    """Ensure exceeding the rate limit returns 429 Too Many Requests."""
    payload = {"email": "limiter_test@example.com", "password": "Password123!"}

    # Hit the endpoint repeatedly to exhaust the quota
    responses = []
    for _ in range(15):
        res = await client.post("/api/auth/register", json=payload)
        responses.append(res.status_code)

    # Confirm that at least one of the requests hit the 429 limit
    assert 429 in responses