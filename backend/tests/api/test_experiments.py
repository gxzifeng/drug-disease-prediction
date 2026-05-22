"""Tests for experiments API endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.models.graph import Graph
from app.models.embedding import Embedding
from app.models.experiment import Experiment


@pytest.fixture
async def test_experiment_chain(db_session: AsyncSession) -> dict:
    """Create a complete chain: dataset -> graph -> embedding -> experiment."""
    # Create dataset
    dataset = Dataset(
        name="Exp Test Dataset",
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
    
    # Create graph
    graph = Graph(
        name="Exp Test Graph",
        dataset_id=dataset.id,
        is_built=True,
        node_count=10,
        edge_count=10,
        drug_count=5,
        disease_count=5,
    )
    db_session.add(graph)
    await db_session.flush()
    
    # Create embedding
    embedding = Embedding(
        name="Exp Test Embedding",
        graph_id=graph.id,
        method="node2vec",
        dimension=64,
        status="completed",
        file_path="/tmp/embedding.npy",
    )
    db_session.add(embedding)
    await db_session.flush()
    
    # Create experiment
    experiment = Experiment(
        name="Exp Test Experiment",
        embedding_id=embedding.id,
        classifier="random_forest",
        feature_method="hadamard",
        status="completed",
        auc_roc=0.85,
        auc_pr=0.78,
        f1_score=0.75,
    )
    db_session.add(experiment)
    await db_session.commit()
    
    return {
        "dataset": dataset,
        "graph": graph,
        "embedding": embedding,
        "experiment": experiment,
    }


@pytest.mark.asyncio
class TestCreateExperiment:
    """Tests for experiment creation endpoint."""
    
    async def test_create_experiment_success(
        self, client: AsyncClient, auth_headers: dict, test_experiment_chain: dict
    ):
        """Test successful experiment creation."""
        embedding = test_experiment_chain["embedding"]
        
        response = await client.post(
            "/api/v1/experiments",
            headers=auth_headers,
            json={
                "name": "New Experiment",
                "embedding_id": embedding.id,
                "classifier": "random_forest",
                "feature_method": "hadamard",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "New Experiment"
        assert data["data"]["status"] == "pending"
    
    async def test_create_experiment_invalid_embedding(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test experiment creation with invalid embedding ID."""
        response = await client.post(
            "/api/v1/experiments",
            headers=auth_headers,
            json={
                "name": "New Experiment",
                "embedding_id": 99999,
                "classifier": "random_forest",
            }
        )
        assert response.status_code == 404
    
    async def test_create_experiment_invalid_classifier(
        self, client: AsyncClient, auth_headers: dict, test_experiment_chain: dict
    ):
        """Test experiment creation with invalid classifier."""
        embedding = test_experiment_chain["embedding"]
        
        response = await client.post(
            "/api/v1/experiments",
            headers=auth_headers,
            json={
                "name": "New Experiment",
                "embedding_id": embedding.id,
                "classifier": "invalid_classifier",
            }
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestListExperiments:
    """Tests for listing experiments endpoint."""
    
    async def test_list_experiments_empty(self, client: AsyncClient):
        """Test listing experiments when none exist."""
        response = await client.get("/api/v1/experiments")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["items"] == []
    
    async def test_list_experiments_with_filter(
        self, client: AsyncClient, test_experiment_chain: dict
    ):
        """Test listing experiments with classifier filter."""
        response = await client.get(
            "/api/v1/experiments?classifier=random_forest"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) >= 1
        for item in data["data"]["items"]:
            assert item["classifier"] == "random_forest"
    
    async def test_list_experiments_with_status_filter(
        self, client: AsyncClient, test_experiment_chain: dict
    ):
        """Test listing experiments with status filter."""
        response = await client.get(
            "/api/v1/experiments?status=completed"
        )
        assert response.status_code == 200


@pytest.mark.asyncio
class TestGetExperiment:
    """Tests for getting single experiment endpoint."""
    
    async def test_get_experiment_success(
        self, client: AsyncClient, test_experiment_chain: dict
    ):
        """Test getting experiment details."""
        experiment = test_experiment_chain["experiment"]
        
        response = await client.get(f"/api/v1/experiments/{experiment.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == experiment.id
        assert data["data"]["classifier"] == "random_forest"
    
    async def test_get_experiment_not_found(self, client: AsyncClient):
        """Test getting non-existent experiment."""
        response = await client.get("/api/v1/experiments/99999")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestCompareExperiments:
    """Tests for experiment comparison endpoint."""
    
    async def test_compare_experiments_success(
        self, client: AsyncClient, db_session: AsyncSession, test_experiment_chain: dict
    ):
        """Test comparing multiple experiments."""
        embedding = test_experiment_chain["embedding"]
        
        # Create another experiment
        exp2 = Experiment(
            name="Second Experiment",
            embedding_id=embedding.id,
            classifier="xgboost",
            feature_method="concat",
            status="completed",
            auc_roc=0.88,
            auc_pr=0.80,
            f1_score=0.77,
        )
        db_session.add(exp2)
        await db_session.commit()
        
        exp1 = test_experiment_chain["experiment"]
        
        response = await client.post(
            "/api/v1/experiments/compare",
            json=[exp1.id, exp2.id]
        )
        assert response.status_code == 200
        data = response.json()
        assert "experiments" in data["data"]
        assert "metrics_comparison" in data["data"]


@pytest.mark.asyncio
class TestActivateModel:
    """Tests for model activation endpoint."""
    
    async def test_activate_model_success(
        self, client: AsyncClient, auth_headers: dict, test_experiment_chain: dict
    ):
        """Test activating a model."""
        experiment = test_experiment_chain["experiment"]
        
        response = await client.post(
            f"/api/v1/experiments/{experiment.id}/activate",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["is_active"] == True
    
    async def test_activate_model_unauthorized(
        self, client: AsyncClient, test_experiment_chain: dict
    ):
        """Test activating model without auth."""
        experiment = test_experiment_chain["experiment"]
        
        response = await client.post(
            f"/api/v1/experiments/{experiment.id}/activate"
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestDeleteExperiment:
    """Tests for experiment deletion endpoint."""
    
    async def test_delete_experiment_unauthorized(
        self, client: AsyncClient, test_experiment_chain: dict
    ):
        """Test deleting experiment without auth."""
        experiment = test_experiment_chain["experiment"]
        
        response = await client.delete(f"/api/v1/experiments/{experiment.id}")
        assert response.status_code == 401
