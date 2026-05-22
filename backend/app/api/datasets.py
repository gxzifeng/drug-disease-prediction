"""Dataset API endpoints."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.models.user import User
from app.schemas.dataset import (
    DatasetResponse,
    DatasetListResponse,
    DatasetPreviewResponse,
    DatasetStats,
    DatasetUpdate,
)
from app.schemas.response import ResponseModel
from app.services.dataset import DatasetService


router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("", response_model=ResponseModel[DatasetResponse])
async def upload_dataset(
    name: str = Form(..., min_length=1, max_length=200),
    source: str = Form(default="custom", max_length=50),
    description: Optional[str] = Form(default=None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Upload a new dataset.
    
    The file should be a CSV or TSV file with the following columns:
    - drug_id (required): Drug identifier
    - drug_name (optional): Drug name
    - disease_id (required): Disease identifier
    - disease_name (optional): Disease name
    - label (optional): Association label (0 or 1, defaults to 1)
    """
    service = DatasetService(db)
    user_id = current_user.id if current_user else None
    
    dataset = await service.create_dataset(
        name=name,
        source=source,
        description=description,
        file=file,
        user_id=user_id,
    )
    
    return ResponseModel(
        code=200,
        message="Dataset uploaded successfully",
        data=DatasetResponse.model_validate(dataset),
    )


@router.get("", response_model=ResponseModel[DatasetListResponse])
async def list_datasets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    keyword: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """List datasets with optional filtering and pagination."""
    service = DatasetService(db)
    
    result = await service.list_datasets(
        page=page,
        page_size=page_size,
        keyword=keyword,
        source=source,
        start_date=start_date,
        end_date=end_date,
    )
    
    return ResponseModel(
        code=200,
        message="Success",
        data=result,
    )


@router.get("/{dataset_id}", response_model=ResponseModel[DatasetResponse])
async def get_dataset(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get dataset details by ID."""
    service = DatasetService(db)
    dataset = await service.get_dataset_or_404(dataset_id)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=DatasetResponse.model_validate(dataset),
    )


@router.get("/{dataset_id}/preview", response_model=ResponseModel[DatasetPreviewResponse])
async def get_dataset_preview(
    dataset_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated preview of dataset records."""
    service = DatasetService(db)
    result = await service.get_dataset_preview(
        dataset_id=dataset_id,
        page=page,
        page_size=page_size,
    )
    
    return ResponseModel(
        code=200,
        message="Success",
        data=result,
    )


@router.get("/{dataset_id}/stats", response_model=ResponseModel[DatasetStats])
async def get_dataset_stats(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get dataset statistics."""
    service = DatasetService(db)
    stats = await service.get_dataset_stats(dataset_id)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=stats,
    )


@router.put("/{dataset_id}", response_model=ResponseModel[DatasetResponse])
async def update_dataset(
    dataset_id: int,
    update_data: DatasetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update dataset metadata."""
    service = DatasetService(db)
    dataset = await service.update_dataset(dataset_id, update_data)
    
    return ResponseModel(
        code=200,
        message="Dataset updated successfully",
        data=DatasetResponse.model_validate(dataset),
    )


@router.delete("/{dataset_id}", response_model=ResponseModel)
async def delete_dataset(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a dataset."""
    service = DatasetService(db)
    await service.delete_dataset(dataset_id)
    
    return ResponseModel(
        code=200,
        message="Dataset deleted successfully",
    )
