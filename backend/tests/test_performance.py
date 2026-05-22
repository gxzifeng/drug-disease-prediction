"""Performance tests and benchmarks for the application."""
import pytest
import time
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset, DatasetRecord


@pytest.fixture
async def large_dataset(db_session: AsyncSession) -> Dataset:
    """Create a larger dataset for performance testing."""
    dataset = Dataset(
        name="Large Performance Dataset",
        source="performance_test",
        original_filename="large.csv",
        file_path="/tmp/large.csv",
        file_size=100000,
        drug_count=100,
        disease_count=100,
        association_count=1000,
        positive_count=800,
        negative_count=200,
        is_parsed=True,
    )
    db_session.add(dataset)
    await db_session.flush()
    
    # Create 1000 records
    records = []
    for i in range(1000):
        drug_idx = i % 100
        disease_idx = (i // 10) % 100
        records.append(DatasetRecord(
            dataset_id=dataset.id,
            drug_id=f"DRUG_{drug_idx:04d}",
            drug_name=f"Drug {drug_idx}",
            disease_id=f"DISEASE_{disease_idx:04d}",
            disease_name=f"Disease {disease_idx}",
            label=1 if i % 5 != 0 else 0,
        ))
    
    db_session.add_all(records)
    await db_session.commit()
    await db_session.refresh(dataset)
    return dataset


class TestResponseTime:
    """Tests for API response time benchmarks."""
    
    @pytest.mark.asyncio
    async def test_health_check_response_time(self, client: AsyncClient):
        """Health check should respond within 100ms."""
        start = time.time()
        response = await client.get("/api/v1/health")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.1, f"Health check took {elapsed:.3f}s, expected < 0.1s"
    
    @pytest.mark.asyncio
    async def test_dataset_list_response_time(self, client: AsyncClient, large_dataset: Dataset):
        """Dataset listing should respond within 500ms."""
        start = time.time()
        response = await client.get("/api/v1/datasets?page=1&page_size=20")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5, f"Dataset list took {elapsed:.3f}s, expected < 0.5s"
    
    @pytest.mark.asyncio
    async def test_dataset_preview_response_time(
        self, client: AsyncClient, large_dataset: Dataset
    ):
        """Dataset preview should respond within 500ms."""
        start = time.time()
        response = await client.get(
            f"/api/v1/datasets/{large_dataset.id}/preview?page=1&page_size=100"
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5, f"Dataset preview took {elapsed:.3f}s, expected < 0.5s"
    
    @pytest.mark.asyncio
    async def test_dataset_stats_response_time(
        self, client: AsyncClient, large_dataset: Dataset
    ):
        """Dataset stats should respond within 200ms."""
        start = time.time()
        response = await client.get(f"/api/v1/datasets/{large_dataset.id}/stats")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.2, f"Dataset stats took {elapsed:.3f}s, expected < 0.2s"


class TestConcurrentLoad:
    """Tests for concurrent request handling."""
    
    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, client: AsyncClient):
        """Test 50 concurrent health check requests."""
        async def health_check():
            return await client.get("/api/v1/health")
        
        start = time.time()
        tasks = [health_check() for _ in range(50)]
        responses = await asyncio.gather(*tasks)
        elapsed = time.time() - start
        
        # All should succeed
        for r in responses:
            assert r.status_code == 200
        
        # All 50 requests should complete within 5 seconds
        assert elapsed < 5.0, f"50 health checks took {elapsed:.3f}s, expected < 5s"
    
    @pytest.mark.asyncio
    async def test_concurrent_dataset_reads(
        self, client: AsyncClient, large_dataset: Dataset
    ):
        """Test 20 concurrent dataset read requests."""
        async def read_dataset():
            return await client.get(f"/api/v1/datasets/{large_dataset.id}")
        
        start = time.time()
        tasks = [read_dataset() for _ in range(20)]
        responses = await asyncio.gather(*tasks)
        elapsed = time.time() - start
        
        # All should succeed
        for r in responses:
            assert r.status_code == 200
        
        # All 20 requests should complete within 3 seconds
        assert elapsed < 3.0, f"20 dataset reads took {elapsed:.3f}s, expected < 3s"


class TestMemoryEfficiency:
    """Tests for memory-efficient operations."""
    
    @pytest.mark.asyncio
    async def test_paginated_preview_memory(
        self, client: AsyncClient, large_dataset: Dataset
    ):
        """Ensure paginated preview doesn't load all records."""
        # Request small page
        response = await client.get(
            f"/api/v1/datasets/{large_dataset.id}/preview?page=1&page_size=10"
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should only return requested page size
        assert len(data["data"]["records"]) == 10
        # But total should reflect all records
        assert data["data"]["total"] == 1000


class TestSearchPerformance:
    """Tests for search functionality performance."""
    
    @pytest.mark.asyncio
    async def test_keyword_search_response_time(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Keyword search should respond within 500ms."""
        # Create multiple datasets with various names
        for i in range(30):
            dataset = Dataset(
                name=f"Searchable Dataset {i} - Type {'A' if i % 2 == 0 else 'B'}",
                source="search_test",
                original_filename=f"search_{i}.csv",
                file_path=f"/tmp/search_{i}.csv",
                file_size=1000,
                is_parsed=True,
            )
            db_session.add(dataset)
        await db_session.commit()
        
        start = time.time()
        response = await client.get("/api/v1/datasets?keyword=Type A")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5, f"Search took {elapsed:.3f}s, expected < 0.5s"


class TestDatabaseQueryOptimization:
    """Tests to ensure database queries are optimized."""
    
    @pytest.mark.asyncio
    async def test_list_with_all_filters(
        self, client: AsyncClient, large_dataset: Dataset
    ):
        """Test listing with multiple filters applied."""
        start = time.time()
        response = await client.get(
            "/api/v1/datasets",
            params={
                "page": 1,
                "page_size": 10,
                "keyword": "Performance",
                "source": "performance_test",
            }
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5, f"Filtered list took {elapsed:.3f}s, expected < 0.5s"


class TestBatchOperations:
    """Tests for batch operation efficiency."""
    
    @pytest.mark.asyncio
    async def test_batch_file_upload_processing(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test uploading a moderately sized CSV file."""
        # Create a CSV with 500 records
        lines = ["drug_id,disease_id,drug_name,disease_name,label"]
        for i in range(500):
            lines.append(f"DRUG_{i:04d},DISEASE_{i % 50:04d},Drug {i},Disease {i % 50},1")
        csv_content = "\n".join(lines).encode('utf-8')
        
        files = {"file": ("batch_test.csv", csv_content, "text/csv")}
        
        start = time.time()
        response = await client.post(
            "/api/v1/datasets",
            data={"name": "Batch Upload Test", "source": "batch_test"},
            files=files,
            headers=auth_headers,
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        # 500 records should be processed within 5 seconds
        assert elapsed < 5.0, f"Batch upload took {elapsed:.3f}s, expected < 5s"
        
        data = response.json()
        assert data["data"]["association_count"] == 500
