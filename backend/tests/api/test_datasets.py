import pytest
from httpx import AsyncClient
import io

@pytest.mark.asyncio
async def test_create_dataset_no_auth(client: AsyncClient):
    response = await client.post("/api/v1/datasets", data={"name": "test", "source": "test"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_datasets_empty(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/datasets", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "items" in data["data"]
    assert len(data["data"]["items"]) == 0

@pytest.mark.asyncio
async def test_upload_empty_file(client: AsyncClient, auth_headers: dict):
    files = {"file": ("empty.csv", b"", "text/csv")}
    response = await client.post(
        "/api/v1/datasets", 
        data={"name": "empty", "source": "test"},
        files=files,
        headers=auth_headers
    )
    assert response.status_code == 400
    assert "empty" in response.json()["message"]
