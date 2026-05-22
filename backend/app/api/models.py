"""Model registry API endpoints (alias for completed experiments)."""
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.experiment import (
    ExperimentResponse,
    ExperimentListResponse,
    ExperimentDetail,
    ExperimentComparison,
)
from app.schemas.response import ResponseModel
from app.services.experiment import ExperimentService


router = APIRouter(prefix="/models", tags=["Models"])


@router.get("", response_model=ResponseModel[ExperimentListResponse])
async def list_models(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    keyword: Optional[str] = Query(default=None),
    classifier: Optional[str] = Query(default=None, pattern="^(random_forest|xgboost|svm)$"),
    db: AsyncSession = Depends(get_db),
):
    """
    List registered models (completed experiments).
    """
    service = ExperimentService(db)
    
    # We only want completed experiments that have a model file
    result = await service.list_experiments(
        page=page,
        page_size=page_size,
        keyword=keyword,
        classifier=classifier,
        status="completed",
    )
    
    return ResponseModel(
        code=200,
        message="Success",
        data=result,
    )


@router.get("/active", response_model=ResponseModel[ExperimentResponse])
async def get_active_model(
    db: AsyncSession = Depends(get_db),
):
    """Get the currently active model for predictions."""
    service = ExperimentService(db)
    experiment = await service.get_active_model()
    
    if not experiment:
        return ResponseModel(
            code=404,
            message="No active model found",
            data=None,
        )
    
    return ResponseModel(
        code=200,
        message="Success",
        data=ExperimentResponse.model_validate(experiment),
    )


@router.get("/{model_id}", response_model=ResponseModel[ExperimentDetail])
async def get_model_detail(
    model_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get model details by ID."""
    service = ExperimentService(db)
    detail = await service.get_experiment_detail(model_id)
    
    # Check if it's a completed experiment
    if detail.status != "completed":
        raise HTTPException(status_code=400, detail="Experiment is not completed")
    
    return ResponseModel(
        code=200,
        message="Success",
        data=detail,
    )


@router.post("/{model_id}/activate", response_model=ResponseModel[ExperimentResponse])
async def activate_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set a model as the active model for predictions."""
    service = ExperimentService(db)
    
    # First check if it's completed
    experiment = await service.get_experiment_or_404(model_id)
    if experiment.status != "completed":
        raise HTTPException(status_code=400, detail="Only completed models can be activated")
    
    experiment = await service.set_active_model(model_id)
    
    return ResponseModel(
        code=200,
        message="Model activated successfully",
        data=ExperimentResponse.model_validate(experiment),
    )


@router.post("/compare", response_model=ResponseModel[ExperimentComparison])
async def compare_models(
    model_ids: List[int],
    db: AsyncSession = Depends(get_db),
):
    """Compare multiple models by their metrics."""
    service = ExperimentService(db)
    comparison = await service.compare_experiments(model_ids)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=ExperimentComparison(**comparison),
    )


@router.delete("/{model_id}", response_model=ResponseModel)
async def delete_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a model and its associated files."""
    service = ExperimentService(db)
    await service.delete_experiment(model_id)
    
    return ResponseModel(
        code=200,
        message="Model deleted successfully",
    )
