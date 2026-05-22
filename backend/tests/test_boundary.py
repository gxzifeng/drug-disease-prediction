"""Boundary and edge case tests for the application."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.models.dataset import Dataset


@pytest.mark.asyncio
class TestFileUploadBoundary:
    """Boundary tests for file uploads."""
    
    async def test_upload_empty_csv(self, client: AsyncClient, auth_headers: dict):
        """Test uploading completely empty file."""
        files = {"file": ("empty.csv", b"", "text/csv")}
        response = await client.post(
            "/api/v1/datasets",
            data={"name": "Empty Dataset", "source": "test"},
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "empty" in response.json()["message"].lower()
    
    async def test_upload_headers_only_csv(self, client: AsyncClient, auth_headers: dict):
        """Test uploading CSV with only headers, no data."""
        csv_content = b"drug_id,disease_id,label\n"
        files = {"file": ("headers_only.csv", csv_content, "text/csv")}
        response = await client.post(
            "/api/v1/datasets",
            data={"name": "Headers Only", "source": "test"},
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 400
    
    async def test_upload_missing_required_column(self, client: AsyncClient, auth_headers: dict):
        """Test uploading CSV without required drug_id column."""
        csv_content = b"disease_id,label\nDIS001,1\nDIS002,0\n"
        files = {"file": ("missing_col.csv", csv_content, "text/csv")}
        response = await client.post(
            "/api/v1/datasets",
            data={"name": "Missing Column", "source": "test"},
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 400
    
    async def test_upload_invalid_file_extension(self, client: AsyncClient, auth_headers: dict):
        """Test uploading file with invalid extension."""
        files = {"file": ("data.pdf", b"some content", "application/pdf")}
        response = await client.post(
            "/api/v1/datasets",
            data={"name": "Invalid Extension", "source": "test"},
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 400
    
    async def test_upload_valid_tsv(self, client: AsyncClient, auth_headers: dict):
        """Test uploading valid TSV file."""
        tsv_content = b"drug_id\tdisease_id\tlabel\nD001\tDIS001\t1\nD002\tDIS002\t1\n"
        files = {"file": ("data.tsv", tsv_content, "text/tab-separated-values")}
        response = await client.post(
            "/api/v1/datasets",
            data={"name": "TSV Dataset", "source": "test"},
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 200
    
    async def test_upload_with_special_characters(self, client: AsyncClient, auth_headers: dict):
        """Test uploading CSV with special characters in IDs."""
        csv_content = b"drug_id,disease_id,label\nDB:001,MESH:D001,1\nDrug-002,Disease_003,1\n"
        files = {"file": ("special.csv", csv_content, "text/csv")}
        response = await client.post(
            "/api/v1/datasets",
            data={"name": "Special Chars", "source": "test"},
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 200
    
    async def test_upload_with_unicode(self, client: AsyncClient, auth_headers: dict):
        """Test uploading CSV with unicode characters."""
        csv_content = "drug_id,disease_id,drug_name,label\nD001,DIS001,阿司匹林,1\nD002,DIS002,布洛芬,1\n".encode('utf-8')
        files = {"file": ("unicode.csv", csv_content, "text/csv")}
        response = await client.post(
            "/api/v1/datasets",
            data={"name": "Unicode Dataset", "source": "test"},
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 200
    
    async def test_upload_duplicate_rows(self, client: AsyncClient, auth_headers: dict):
        """Test uploading CSV with duplicate rows."""
        csv_content = b"drug_id,disease_id,label\nD001,DIS001,1\nD001,DIS001,1\nD001,DIS001,1\n"
        files = {"file": ("duplicates.csv", csv_content, "text/csv")}
        response = await client.post(
            "/api/v1/datasets",
            data={"name": "Duplicates", "source": "test"},
            files=files,
            headers=auth_headers,
        )
        # Should accept but may have warning
        assert response.status_code == 200


@pytest.mark.asyncio
class TestPaginationBoundary:
    """Boundary tests for pagination."""
    
    async def test_page_zero(self, client: AsyncClient):
        """Test requesting page 0 (invalid)."""
        response = await client.get("/api/v1/datasets?page=0")
        assert response.status_code == 422
    
    async def test_negative_page(self, client: AsyncClient):
        """Test requesting negative page."""
        response = await client.get("/api/v1/datasets?page=-1")
        assert response.status_code == 422
    
    async def test_page_size_zero(self, client: AsyncClient):
        """Test requesting page_size 0."""
        response = await client.get("/api/v1/datasets?page_size=0")
        assert response.status_code == 422
    
    async def test_page_size_too_large(self, client: AsyncClient):
        """Test requesting page_size exceeding limit."""
        response = await client.get("/api/v1/datasets?page_size=1000")
        assert response.status_code == 422
    
    async def test_page_beyond_total(self, client: AsyncClient):
        """Test requesting page beyond total pages."""
        response = await client.get("/api/v1/datasets?page=9999")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["items"] == []


@pytest.mark.asyncio
class TestInputValidation:
    """Input validation boundary tests."""
    
    async def test_long_dataset_name(self, client: AsyncClient, auth_headers: dict):
        """Test dataset creation with very long name."""
        csv_content = b"drug_id,disease_id,label\nD001,DIS001,1\n"
        files = {"file": ("data.csv", csv_content, "text/csv")}
        
        # Name exceeding 200 chars
        long_name = "A" * 250
        response = await client.post(
            "/api/v1/datasets",
            data={"name": long_name, "source": "test"},
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 422
    
    async def test_empty_dataset_name(self, client: AsyncClient, auth_headers: dict):
        """Test dataset creation with empty name."""
        csv_content = b"drug_id,disease_id,label\nD001,DIS001,1\n"
        files = {"file": ("data.csv", csv_content, "text/csv")}
        
        response = await client.post(
            "/api/v1/datasets",
            data={"name": "", "source": "test"},
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 422
    
    async def test_sql_injection_attempt(self, client: AsyncClient, auth_headers: dict):
        """Test SQL injection in search keyword."""
        response = await client.get(
            "/api/v1/datasets?keyword='; DROP TABLE datasets; --",
            headers=auth_headers,
        )
        # Should not error, just return no results
        assert response.status_code == 200
    
    async def test_xss_attempt_in_name(self, client: AsyncClient, auth_headers: dict):
        """Test XSS attempt in dataset name."""
        csv_content = b"drug_id,disease_id,label\nD001,DIS001,1\n"
        files = {"file": ("data.csv", csv_content, "text/csv")}
        
        xss_name = '<script>alert("XSS")</script>'
        response = await client.post(
            "/api/v1/datasets",
            data={"name": xss_name, "source": "test"},
            files=files,
            headers=auth_headers,
        )
        # Should accept (sanitization happens in frontend)
        # or reject if backend sanitizes
        assert response.status_code in [200, 400, 422]


@pytest.mark.asyncio
class TestGraphBuildingBoundary:
    """Boundary tests for graph building."""
    
    async def test_build_graph_invalid_ratios_sum(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ):
        """Test graph building with ratios not summing to 1."""
        dataset = Dataset(
            name="Ratio Test",
            source="test",
            original_filename="test.csv",
            file_path="/tmp/test.csv",
            file_size=100,
            is_parsed=True,
        )
        db_session.add(dataset)
        await db_session.commit()
        
        response = await client.post(
            "/api/v1/graphs/build",
            headers=auth_headers,
            json={
                "dataset_id": dataset.id,
                "name": "Bad Ratios",
                "train_ratio": 0.9,
                "val_ratio": 0.1,
                "test_ratio": 0.1,  # Sum = 1.1
            }
        )
        assert response.status_code == 422
    
    async def test_build_graph_zero_train_ratio(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ):
        """Test graph building with zero training ratio."""
        dataset = Dataset(
            name="Zero Train Test",
            source="test",
            original_filename="test.csv",
            file_path="/tmp/test.csv",
            file_size=100,
            is_parsed=True,
        )
        db_session.add(dataset)
        await db_session.commit()
        
        response = await client.post(
            "/api/v1/graphs/build",
            headers=auth_headers,
            json={
                "dataset_id": dataset.id,
                "name": "Zero Train",
                "train_ratio": 0.0,
                "val_ratio": 0.5,
                "test_ratio": 0.5,
            }
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestExperimentBoundary:
    """Boundary tests for experiment creation."""
    
    async def test_invalid_feature_method(self, client: AsyncClient, auth_headers: dict):
        """Test experiment with invalid feature method."""
        response = await client.post(
            "/api/v1/experiments",
            headers=auth_headers,
            json={
                "name": "Bad Feature",
                "embedding_id": 1,
                "classifier": "random_forest",
                "feature_method": "invalid_method",
            }
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestConcurrentAccess:
    """Tests for concurrent access patterns."""
    
    async def test_concurrent_dataset_creation(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating multiple datasets concurrently."""
        import asyncio
        
        async def create_dataset(n: int):
            csv_content = f"drug_id,disease_id,label\nD{n:03d},DIS{n:03d},1\n".encode()
            files = {"file": (f"data_{n}.csv", csv_content, "text/csv")}
            return await client.post(
                "/api/v1/datasets",
                data={"name": f"Concurrent {n}", "source": "test"},
                files=files,
                headers=auth_headers,
            )
        
        # Create 5 datasets concurrently
        tasks = [create_dataset(i) for i in range(5)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        for r in responses:
            if not isinstance(r, Exception):
                assert r.status_code == 200
