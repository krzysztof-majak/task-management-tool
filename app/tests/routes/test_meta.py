import pytest
from fastapi import status
from httpx import AsyncClient, Response


@pytest.mark.asyncio
async def test_health_endpoint(test_api_client: AsyncClient) -> None:
    response: Response = await test_api_client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert "Swagger UI" in response.text
