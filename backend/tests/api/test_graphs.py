"""Tests for graphs API endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset, DatasetRecord
from app.models.graph import Graph


@pytest.fixture
async def test_dataset(db_session: AsyncSession) -> Dataset:
    """Create a test dataset with records."""
    dataset = Dataset(
        name="Test Dataset",
        source="test",
        original_filename="test.csv",
        file_path="/tmp/test.csv",
        file_size=1000,
        drug_count=3,
        disease_count=3,
        association_count=4,
        positive_count=4,
        negative_count=0,
        is_parsed=True,
    )
    db_session.add(dataset)
    await db_session.flush()
    
    # Add test records
    records = [
        DatasetRecord(dataset_id=dataset.id, drug_id="D001", disease_id="DIS001", label=1),
        DatasetRecord(dataset_id=dataset.id, drug_id="D001", disease_id="DIS002", label=1),
        DatasetRecord(dataset_id=dataset.id, drug_id="D002", disease_id="DIS001", label=1),
        DatasetRecord(dataset_id=dataset.id, drug_id="D002", disease_id="DIS003", label=1),
    ]
    for r in records:
        db_session.add(r)
    
    await db_session.commit()
    await db_session.refresh(dataset)
    return dataset


@pytest.mark.asyncio
class TestBuildGraph:
    """Tests for graph building endpoint."""
    
    async def test_build_graph_success(
        self, client: AsyncClient, auth_headers: dict, test_dataset: Dataset
    ):
        """Test successful graph building."""
        response = await client.post(
            "/api/v1/graphs/build",
            headers=auth_headers,
            json={
                "dataset_id": test_dataset.id,
                "name": "Test Graph",
                "train_ratio": 0.8,
                "val_ratio": 0.1,
                "test_ratio": 0.1,
                "negative_ratio": 1.0,
                "random_seed": 42,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["name"] == "Test Graph"
    
    async def test_build_graph_invalid_dataset(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test building graph with invalid dataset ID."""
        response = await client.post(
            "/api/v1/graphs/build",
            headers=auth_headers,
            json={
                "dataset_id": 99999,  # Non-existent
                "name": "Test Graph",
            }
        )
        assert response.status_code == 404
    
    async def test_build_graph_invalid_ratios(
        self, client: AsyncClient, auth_headers: dict, test_dataset: Dataset
    ):
        """Test building graph with invalid split ratios."""
        response = await client.post(
            "/api/v1/graphs/build",
            headers=auth_headers,
            json={
                "dataset_id": test_dataset.id,
                "name": "Test Graph",
                "train_ratio": 0.5,
                "val_ratio": 0.3,
                "test_ratio": 0.3,  # Sum > 1.0
            }
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestListGraphs:
    """Tests for listing graphs endpoint."""
    
    async def test_list_graphs_empty(self, client: AsyncClient):
        """Test listing graphs when none exist."""
        response = await client.get("/api/v1/graphs")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["items"] == []
    
    async def test_list_graphs_pagination(
        self, client: AsyncClient, db_session: AsyncSession, test_dataset: Dataset
    ):
        """Test graph listing with pagination."""
        # Create multiple graphs
        for i in range(15):
            graph = Graph(
                name=f"Graph {i}",
                dataset_id=test_dataset.id,
            )
            db_session.add(graph)
        await db_session.commit()
        
        # Test first page
        response = await client.get("/api/v1/graphs?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) == 10
        assert data["data"]["total"] == 15
        assert data["data"]["pages"] == 2
        
        # Test second page
        response = await client.get("/api/v1/graphs?page=2&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) == 5


@pytest.mark.asyncio
class TestGetGraph:
    """Tests for getting single graph endpoint."""
    
    async def test_get_graph_not_found(self, client: AsyncClient):
        """Test getting non-existent graph."""
        response = await client.get("/api/v1/graphs/99999")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestDeleteGraph:
    """Tests for deleting graph endpoint."""
    
    async def test_delete_graph_unauthorized(
        self, client: AsyncClient, db_session: AsyncSession, test_dataset: Dataset
    ):
        """Test deleting graph without authentication."""
        graph = Graph(name="To Delete", dataset_id=test_dataset.id)
        db_session.add(graph)
        await db_session.commit()
        
        response = await client.delete(f"/api/v1/graphs/{graph.id}")
        assert response.status_code == 401
    
    async def test_delete_graph_success(
        self, client: AsyncClient, auth_headers: dict, 
        db_session: AsyncSession, test_dataset: Dataset
    ):
        """Test successful graph deletion."""
        graph = Graph(name="To Delete", dataset_id=test_dataset.id)
        db_session.add(graph)
        await db_session.commit()
        
        response = await client.delete(
            f"/api/v1/graphs/{graph.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
