from typing import TYPE_CHECKING

from fastapi import status

if TYPE_CHECKING:
    from httpx import AsyncClient


async def test_read_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["service"] == "trcks-example-fastapi"
    assert data["status"] == "healthy"
    assert "timestamp" in data
