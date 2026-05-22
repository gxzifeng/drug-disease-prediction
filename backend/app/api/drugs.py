"""Drug API endpoints for drug information management."""
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.response import ResponseModel
from app.schemas.drug import (
    DrugResponse,
    DrugDetailResponse,
    DrugListResponse,
    DrugAssociationsListResponse,
    DrugStatisticsResponse,
)
from app.services.drug import DrugService


router = APIRouter(prefix="/drugs", tags=["Drugs"])


@router.get(
    "",
    response_model=ResponseModel[DrugListResponse],
    summary="List all drugs",
    description="Get a paginated list of drugs with optional filtering by keyword, type, and association status.",
)
async def list_drugs(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    keyword: Optional[str] = Query(default=None, description="Search in name and description"),
    drug_type: Optional[str] = Query(default=None, alias="type", description="Filter by drug type"),
    has_associations: Optional[bool] = Query(default=None, description="Filter by association status"),
    db: AsyncSession = Depends(get_db),
):
    """
    List drugs with pagination and filtering.
    
    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page (1-100)
    - **keyword**: Search keyword for name/description
    - **type**: Filter by drug type (e.g., Interferon, Thrombolytic)
    - **has_associations**: Filter drugs with (true) or without (false) disease associations
    """
    service = DrugService(db)
    result = await service.list_drugs(
        page=page,
        page_size=page_size,
        keyword=keyword,
        drug_type=drug_type,
        has_associations=has_associations,
    )
    
    return ResponseModel(
        code=200,
        message="Success",
        data=result,
    )


@router.get(
    "/statistics",
    response_model=ResponseModel[DrugStatisticsResponse],
    summary="Get drug statistics",
    description="Get overall statistics about drugs including type distribution and top associated drugs.",
)
async def get_drug_statistics(
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive drug statistics.
    
    Returns:
    - Total number of drugs
    - Number of drugs with associations
    - Association counts (total, known, predicted)
    - Drug type distribution
    - Top 10 drugs by association count
    """
    service = DrugService(db)
    result = await service.get_drug_statistics()
    
    return ResponseModel(
        code=200,
        message="Success",
        data=result,
    )


@router.get(
    "/types",
    response_model=ResponseModel[List[str]],
    summary="Get all drug types",
    description="Get a list of all unique drug types for filtering purposes.",
)
async def get_drug_types(
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of all available drug types.
    
    Useful for populating filter dropdowns in the UI.
    """
    service = DrugService(db)
    result = await service.get_drug_types()
    
    return ResponseModel(
        code=200,
        message="Success",
        data=result,
    )


@router.get(
    "/{drug_id}",
    response_model=ResponseModel[DrugDetailResponse],
    summary="Get drug details",
    description="Get detailed information about a specific drug including association statistics.",
)
async def get_drug(
    drug_id: str = Path(..., description="Drug ID (e.g., DB00001)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed drug information by ID.
    
    Returns drug details including:
    - Basic information (name, type, description)
    - Association counts (total, known, predicted)
    - Timestamps
    """
    service = DrugService(db)
    result = await service.get_drug_or_404(drug_id)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=result,
    )


@router.get(
    "/{drug_id}/associations",
    response_model=ResponseModel[DrugAssociationsListResponse],
    summary="Get drug associations",
    description="Get all disease associations for a specific drug.",
)
async def get_drug_associations(
    drug_id: str = Path(..., description="Drug ID (e.g., DB00001)"),
    association_type: Optional[str] = Query(
        default=None,
        pattern="^(known|predicted)$",
        description="Filter by association type: 'known' or 'predicted'"
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of associations to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get disease associations for a drug.
    
    Returns all diseases associated with the specified drug, including:
    - Disease information (ID, name, category)
    - Association type (known/predicted)
    - Confidence score
    
    Results are sorted by confidence score (descending).
    """
    service = DrugService(db)
    result = await service.get_drug_associations(
        drug_id=drug_id,
        association_type=association_type,
        limit=limit,
    )
    
    return ResponseModel(
        code=200,
        message="Success",
        data=result,
    )
