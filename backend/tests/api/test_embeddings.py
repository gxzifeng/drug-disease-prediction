"""Tests for embeddings API endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.models.graph import Graph
from app.models.embedding import Embedding


@pytest.fixture
async def test_graph(db_session: AsyncSession) -> Graph:
    """Create a test graph with dataset."""
    dataset = Dataset(
        name="Embedding Test Dataset",
        source="test",
        original_filename="test.csv",
        file_path="/tmp/test.csv",
        file_size=1000,
        drug_count=5,
        disease_count=5,
        association_count=10,
        positive_count=10,
        negative_count=0,
        is_parsed=True,
    )
    db_session.add(dataset)
    await db_session.flush()
    
    graph = Graph(
        name="Embedding Test Graph",
        dataset_id=dataset.id,
        is_built=True,
        node_count=10,
        edge_count=10,
        drug_count=5,
        disease_count=5,
        node_index_path="/tmp/node_index.json",
        edge_index_path="/tmp/edge_index.npy",
    )
    db_session.add(graph)
    await db_session.commit()
    await db_session.refresh(graph)
    return graph


@pytest.mark.asyncio
class TestCreateEmbedding:
    """Tests for embedding creation endpoint."""
    
    async def test_create_embedding_node2vec(
        self, client: AsyncClient, auth_headers: dict, test_graph: Graph
    ):
        """Test creating Node2Vec embedding."""
        response = await client.post(
            "/api/v1/embeddings/train",
            headers=auth_headers,
            json={
                "name": "Test Node2Vec",
                "graph_id": test_graph.id,
                "method": "node2vec",
                "dimension": 64,
                "params": {
                    "walk_length": 40,
                    "num_walks": 10,
                    "p": 1.0,
                    "q": 1.0,
                    "window_size": 5,
                    "epochs": 1,
                }
            }
        )
        assert response.status_code in [200, 202]
        if response.status_code == 200:
            data = response.json()
            assert data["data"]["method"] == "node2vec"
    
    async def test_create_embedding_invalid_graph(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating embedding with invalid graph ID."""
        response = await client.post(
            "/api/v1/embeddings/train",
            headers=auth_headers,
            json={
                "name": "Test Embedding",
                "graph_id": 99999,
                "method": "node2vec",
            }
        )
        assert response.status_code == 404
    
    async def test_create_embedding_invalid_method(
        self, client: AsyncClient, auth_headers: dict, test_graph: Graph
    ):
        """Test creating embedding with invalid method."""
        response = await client.post(
            "/api/v1/embeddings/train",
            headers=auth_headers,
            json={
                "name": "Test Embedding",
                "graph_id": test_graph.id,
                "method": "invalid_method",
            }
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestListEmbeddings:
    """Tests for listing embeddings endpoint."""
    
    async def test_list_embeddings_empty(self, client: AsyncClient):
        """Test listing embeddings when none exist."""
        response = await client.get("/api/v1/embeddings")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["items"] == []
    
    async def test_list_embeddings_with_filter(
        self, client: AsyncClient, db_session: AsyncSession, test_graph: Graph
    ):
        """Test listing embeddings with method filter."""
        # Create embeddings
        emb1 = Embedding(
            name="Node2Vec 1",
            graph_id=test_graph.id,
            method="node2vec",
            dimension=64,
            status="completed",
        )
        emb2 = Embedding(
            name="GCN 1",
            graph_id=test_graph.id,
            method="gcn",
            dimension=64,
            status="completed",
        )
        db_session.add_all([emb1, emb2])
        await db_session.commit()
        
        # Filter by method
        response = await client.get("/api/v1/embeddings?method=node2vec")
        assert response.status_code == 200
        data = response.json()
        for item in data["data"]["items"]:
            assert item["method"] == "node2vec"


@pytest.mark.asyncio
class TestGetEmbedding:
    """Tests for getting single embedding endpoint."""
    
    async def test_get_embedding_success(
        self, client: AsyncClient, db_session: AsyncSession, test_graph: Graph
    ):
        """Test getting embedding details."""
        embedding = Embedding(
            name="Test Get Embedding",
            graph_id=test_graph.id,
            method="node2vec",
            dimension=128,
            status="completed",
        )
        db_session.add(embedding)
        await db_session.commit()
        
        response = await client.get(f"/api/v1/embeddings/{embedding.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "Test Get Embedding"
        assert data["data"]["dimension"] == 128
    
    async def test_get_embedding_not_found(self, client: AsyncClient):
        """Test getting non-existent embedding."""
        response = await client.get("/api/v1/embeddings/99999")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestDeleteEmbedding:
    """Tests for deleting embedding endpoint."""
    
    async def test_delete_embedding_unauthorized(
        self, client: AsyncClient, db_session: AsyncSession, test_graph: Graph
    ):
        """Test deleting embedding without auth."""
        embedding = Embedding(
            name="To Delete",
            graph_id=test_graph.id,
            method="node2vec",
            dimension=64,
        )
        db_session.add(embedding)
        await db_session.commit()
        
        response = await client.delete(f"/api/v1/embeddings/{embedding.id}")
        assert response.status_code == 401
    
    async def test_delete_embedding_success(
        self, client: AsyncClient, auth_headers: dict,
        db_session: AsyncSession, test_graph: Graph
    ):
        """Test successful embedding deletion."""
        embedding = Embedding(
            name="To Delete",
            graph_id=test_graph.id,
            method="node2vec",
            dimension=64,
        )
        db_session.add(embedding)
        await db_session.commit()
        
        response = await client.delete(
            f"/api/v1/embeddings/{embedding.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200


@pytest.mark.asyncio
class TestEmbeddingsByGraph:
    """Tests for getting embeddings by graph."""
    
    async def test_get_embeddings_by_graph(
        self, client: AsyncClient, db_session: AsyncSession, test_graph: Graph
    ):
        """Test getting all embeddings for a graph."""
        # Create multiple embeddings for the graph
        for i in range(3):
            emb = Embedding(
                name=f"Graph Embedding {i}",
                graph_id=test_graph.id,
                method="node2vec",
                dimension=64,
            )
            db_session.add(emb)
        await db_session.commit()
        
        response = await client.get(f"/api/v1/embeddings/graph/{test_graph.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 3
