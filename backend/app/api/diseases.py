"""Disease API endpoints for disease information management."""
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.response import ResponseModel
from app.schemas.disease import (
    DiseaseResponse,
    DiseaseDetailResponse,
    DiseaseListResponse,
    DiseaseAssociationsListResponse,
    DiseaseStatisticsResponse,
)
from app.services.disease import DiseaseService


router = APIRouter(prefix="/diseases", tags=["Diseases"])


@router.get(
    "",
    response_model=ResponseModel[DiseaseListResponse],
    summary="List all diseases",
    description="Get a paginated list of diseases with optional filtering by keyword, category, and association status.",
)
async def list_diseases(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    keyword: Optional[str] = Query(default=None, description="Search in name and description"),
    category: Optional[str] = Query(default=None, description="Filter by disease category"),
    has_associations: Optional[bool] = Query(default=None, description="Filter by association status"),
    db: AsyncSession = Depends(get_db),
):
    """
    List diseases with pagination and filtering.
    
    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page (1-100)
    - **keyword**: Search keyword for name/description
    - **category**: Filter by disease category (e.g., Cancer, Cardiovascular Disease)
    - **has_associations**: Filter diseases with (true) or without (false) drug associations
    """
    service = DiseaseService(db)
    result = await service.list_diseases(
        page=page,
        page_size=page_size,
        keyword=keyword,
        category=category,
        has_associations=has_associations,
    )
    
    return ResponseModel(
        code=200,
        message="Success",
        data=result,
    )


@router.get(
    "/statistics",
    response_model=ResponseModel[DiseaseStatisticsResponse],
    summary="Get disease statistics",
    description="Get overall statistics about diseases including category distribution and top associated diseases.",
)
async def get_disease_statistics(
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive disease statistics.
    
    Returns:
    - Total number of diseases
    - Number of diseases with associations
    - Association counts (total, known, predicted)
    - Disease category distribution
    - Top 10 diseases by association count
    """
    service = DiseaseService(db)
    result = await service.get_disease_statistics()
    
    return ResponseModel(
        code=200,
        message="Success",
        data=result,
    )


@router.get(
    "/categories",
    response_model=ResponseModel[List[str]],
    summary="Get all disease categories",
    description="Get a list of all unique disease categories for filtering purposes.",
)
async def get_disease_categories(
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of all available disease categories.
    
    Useful for populating filter dropdowns in the UI.
    """
    service = DiseaseService(db)
    result = await service.get_disease_categories()
    
    return ResponseModel(
        code=200,
        message="Success",
        data=result,
    )


@router.get(
    "/{disease_id}",
    response_model=ResponseModel[DiseaseDetailResponse],
    summary="Get disease details",
    description="Get detailed information about a specific disease including association statistics.",
)
async def get_disease(
    disease_id: str = Path(..., description="Disease ID (e.g., DOID:1612)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed disease information by ID.
    
    Returns disease details including:
    - Basic information (name, category, description)
    - Association counts (total, known, predicted)
    - Timestamps
    """
    service = DiseaseService(db)
    result = await service.get_disease_or_404(disease_id)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=result,
    )


@router.get(
    "/{disease_id}/associations",
    response_model=ResponseModel[DiseaseAssociationsListResponse],
    summary="Get disease associations",
    description="Get all drug associations for a specific disease.",
)
async def get_disease_associations(
    disease_id: str = Path(..., description="Disease ID (e.g., DOID:1612)"),
    association_type: Optional[str] = Query(
        default=None,
        pattern="^(known|predicted)$",
        description="Filter by association type: 'known' or 'predicted'"
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of associations to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get drug associations for a disease.
    
    Returns all drugs associated with the specified disease, including:
    - Drug information (ID, name, type)
    - Association type (known/predicted)
    - Confidence score
    
    Results are sorted by confidence score (descending).
    """
    service = DiseaseService(db)
    result = await service.get_disease_associations(
        disease_id=disease_id,
        association_type=association_type,
        limit=limit,
    )
    
    return ResponseModel(
        code=200,
        message="Success",
        data=result,
    )
