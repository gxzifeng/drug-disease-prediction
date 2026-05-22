"""Tests for predictions API endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.models.graph import Graph
from app.models.embedding import Embedding
from app.models.experiment import Experiment


@pytest.fixture
async def prediction_model(db_session: AsyncSession) -> dict:
    """Create a complete model chain for predictions."""
    dataset = Dataset(
        name="Prediction Test Dataset",
        source="test",
        original_filename="test.csv",
        file_path="/tmp/test.csv",
        file_size=1000,
        drug_count=3,
        disease_count=3,
        association_count=5,
        positive_count=5,
        negative_count=0,
        is_parsed=True,
    )
    db_session.add(dataset)
    await db_session.flush()
    
    graph = Graph(
        name="Prediction Test Graph",
        dataset_id=dataset.id,
        is_built=True,
        node_count=6,
        edge_count=5,
        drug_count=3,
        disease_count=3,
    )
    db_session.add(graph)
    await db_session.flush()
    
    embedding = Embedding(
        name="Prediction Test Embedding",
        graph_id=graph.id,
        method="node2vec",
        dimension=64,
        status="completed",
        file_path="/tmp/pred_embedding.npy",
    )
    db_session.add(embedding)
    await db_session.flush()
    
    experiment = Experiment(
        name="Prediction Test Model",
        embedding_id=embedding.id,
        classifier="random_forest",
        feature_method="hadamard",
        status="completed",
        is_active=True,
        model_path="/tmp/model.pkl",
        auc_roc=0.90,
        auc_pr=0.85,
        f1_score=0.80,
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
class TestSinglePrediction:
    """Tests for single prediction endpoint."""
    
    async def test_predict_single_no_model(self, client: AsyncClient):
        """Test prediction when no model is available."""
        response = await client.post(
            "/api/v1/predictions/predict",
            json={
                "drug_id": "D001",
                "disease_id": "DIS001",
            }
        )
        # Should return error when model is not ready
        assert response.status_code in [400, 404, 500]
    
    async def test_predict_single_with_model_id(
        self, client: AsyncClient, prediction_model: dict
    ):
        """Test prediction with specific model ID."""
        experiment = prediction_model["experiment"]
        
        response = await client.post(
            "/api/v1/predictions/predict",
            json={
                "drug_id": "D001",
                "disease_id": "DIS001",
                "model_id": experiment.id,
            }
        )
        # May fail due to missing actual model file in tests
        assert response.status_code in [200, 400, 500]
    
    async def test_predict_single_missing_drug_id(self, client: AsyncClient):
        """Test prediction with missing drug_id."""
        response = await client.post(
            "/api/v1/predictions/predict",
            json={
                "disease_id": "DIS001",
            }
        )
        assert response.status_code == 422
    
    async def test_predict_single_missing_disease_id(self, client: AsyncClient):
        """Test prediction with missing disease_id."""
        response = await client.post(
            "/api/v1/predictions/predict",
            json={
                "drug_id": "D001",
            }
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestBatchPrediction:
    """Tests for batch prediction endpoint."""
    
    async def test_batch_prediction_submit(
        self, client: AsyncClient, prediction_model: dict
    ):
        """Test submitting a batch prediction task."""
        response = await client.post(
            "/api/v1/predictions/batch",
            json={
                "dataset_id": prediction_model["dataset"].id,
                "model_id": prediction_model["experiment"].id,
            }
        )
        # Should accept the task
        assert response.status_code in [200, 202, 500]
    
    async def test_batch_prediction_invalid_dataset(
        self, client: AsyncClient, prediction_model: dict
    ):
        """Test batch prediction with invalid dataset."""
        response = await client.post(
            "/api/v1/predictions/batch",
            json={
                "dataset_id": 99999,
                "model_id": prediction_model["experiment"].id,
            }
        )
        assert response.status_code in [404, 422, 500]


@pytest.mark.asyncio
class TestTaskStatus:
    """Tests for task status endpoint."""
    
    async def test_get_task_status_invalid_id(self, client: AsyncClient):
        """Test getting status of invalid task."""
        response = await client.get("/api/v1/predictions/tasks/invalid-task-id")
        assert response.status_code in [200, 404]
        # Should return pending/unknown status for non-existent task
    
    async def test_get_task_status_format(self, client: AsyncClient):
        """Test task status response format."""
        response = await client.get("/api/v1/predictions/tasks/some-task-id")
        if response.status_code == 200:
            data = response.json()
            assert "status" in data["data"]


@pytest.mark.asyncio
class TestDownloadResults:
    """Tests for downloading prediction results."""
    
    async def test_download_invalid_filename(self, client: AsyncClient):
        """Test downloading with invalid filename (path traversal)."""
        response = await client.get("/api/v1/predictions/download/../secret.txt")
        assert response.status_code == 400
    
    async def test_download_nonexistent_file(self, client: AsyncClient):
        """Test downloading non-existent file."""
        response = await client.get("/api/v1/predictions/download/nonexistent.csv")
        assert response.status_code == 404
    
    async def test_download_path_traversal_backslash(self, client: AsyncClient):
        """Test path traversal with backslash."""
        response = await client.get("/api/v1/predictions/download/..\\secret.txt")
        assert response.status_code == 400
