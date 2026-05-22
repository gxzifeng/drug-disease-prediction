"""Experiment API endpoints."""
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.models.user import User
from app.schemas.experiment import (
    ExperimentTrainRequest,
    ExperimentResponse,
    ExperimentListResponse,
    ExperimentDetail,
    ExperimentUpdate,
    ExperimentComparison,
)
from app.schemas.graph import SubgraphResponse
from app.schemas.response import ResponseModel
from app.services.experiment import ExperimentService
from app.services.prediction import PredictionService
from app.tasks.experiment import run_experiment_training


router = APIRouter(prefix="/experiments", tags=["Experiments"])


@router.post("/train", response_model=ResponseModel[ExperimentResponse])
async def create_and_train_experiment(
    request: ExperimentTrainRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Create and start training a classifier experiment.
    
    This endpoint creates an experiment and starts training immediately.
    Supported classifiers:
    - **random_forest**: Random Forest classifier
    - **xgboost**: XGBoost gradient boosting classifier  
    - **svm**: Support Vector Machine classifier
    
    Feature combination methods:
    - **concat**: Concatenate drug and disease embeddings
    - **hadamard**: Element-wise multiplication
    - **l1**: Absolute difference
    - **l2**: Squared difference
    - **average**: Element-wise average
    """
    service = ExperimentService(db)
    user_id = current_user.id if current_user else None
    
    # Create experiment record
    experiment = await service.create_experiment(request, user_id)
    
    # Start training via Celery
    run_experiment_training.delay(experiment.id)
    
    return ResponseModel(
        code=202,
        message="Experiment training started in background",
        data=ExperimentResponse.model_validate(experiment),
    )


@router.post("", response_model=ResponseModel[ExperimentResponse])
async def create_experiment(
    request: ExperimentTrainRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Create an experiment without starting training."""
    service = ExperimentService(db)
    user_id = current_user.id if current_user else None
    
    experiment = await service.create_experiment(request, user_id)
    
    return ResponseModel(
        code=200,
        message="Experiment created successfully",
        data=ExperimentResponse.model_validate(experiment),
    )


@router.post("/{experiment_id}/start", response_model=ResponseModel[ExperimentResponse])
async def start_training(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start training for an existing experiment."""
    service = ExperimentService(db)
    experiment = await service.get_experiment_or_404(experiment_id)
    
    if experiment.status == "running":
        raise HTTPException(status_code=400, detail="Training is already running")
    
    # Start training via Celery
    run_experiment_training.delay(experiment_id)
    
    return ResponseModel(
        code=202,
        message="Training task submitted",
        data=ExperimentResponse.model_validate(experiment),
    )


@router.get("", response_model=ResponseModel[ExperimentListResponse])
async def list_experiments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    keyword: Optional[str] = Query(default=None),
    embedding_id: Optional[int] = Query(default=None),
    classifier: Optional[str] = Query(default=None, pattern="^(random_forest|xgboost|svm)$"),
    status: Optional[str] = Query(default=None, pattern="^(pending|running|completed|failed)$"),
    db: AsyncSession = Depends(get_db),
):
    """List experiments with optional filtering and pagination."""
    service = ExperimentService(db)
    
    result = await service.list_experiments(
        page=page,
        page_size=page_size,
        keyword=keyword,
        embedding_id=embedding_id,
        classifier=classifier,
        status=status,
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


@router.get("/{experiment_id}", response_model=ResponseModel[ExperimentResponse])
async def get_experiment(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get experiment details by ID."""
    service = ExperimentService(db)
    experiment = await service.get_experiment_or_404(experiment_id)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=ExperimentResponse.model_validate(experiment),
    )


@router.get("/{experiment_id}/detail", response_model=ResponseModel[ExperimentDetail])
async def get_experiment_detail(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed experiment information including metrics and feature importance."""
    service = ExperimentService(db)
    detail = await service.get_experiment_detail(experiment_id)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=detail,
    )


@router.put("/{experiment_id}", response_model=ResponseModel[ExperimentResponse])
async def update_experiment(
    experiment_id: int,
    update_data: ExperimentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update experiment metadata (name, description)."""
    service = ExperimentService(db)
    experiment = await service.update_experiment(experiment_id, update_data)
    
    return ResponseModel(
        code=200,
        message="Experiment updated successfully",
        data=ExperimentResponse.model_validate(experiment),
    )


@router.delete("/{experiment_id}", response_model=ResponseModel)
async def delete_experiment(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an experiment and its associated model files."""
    service = ExperimentService(db)
    await service.delete_experiment(experiment_id)
    
    return ResponseModel(
        code=200,
        message="Experiment deleted successfully",
    )


@router.post("/{experiment_id}/activate", response_model=ResponseModel[ExperimentResponse])
async def activate_model(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set an experiment as the active model for predictions."""
    service = ExperimentService(db)
    experiment = await service.set_active_model(experiment_id)
    
    return ResponseModel(
        code=200,
        message="Model activated successfully",
        data=ExperimentResponse.model_validate(experiment),
    )


@router.post("/compare", response_model=ResponseModel[ExperimentComparison])
async def compare_experiments(
    experiment_ids: List[int],
    db: AsyncSession = Depends(get_db),
):
    """Compare multiple experiments by their metrics."""
    service = ExperimentService(db)
    comparison = await service.compare_experiments(experiment_ids)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=ExperimentComparison(**comparison),
    )


@router.get("/embedding/{embedding_id}", response_model=ResponseModel[List[ExperimentResponse]])
async def get_experiments_by_embedding(
    embedding_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all experiments for a specific embedding."""
    service = ExperimentService(db)
    experiments = await service.get_experiments_by_embedding(embedding_id)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=[ExperimentResponse.model_validate(e) for e in experiments],
    )


@router.get("/{experiment_id}/top-predictions", response_model=ResponseModel[SubgraphResponse])
async def get_top_predictions(
    experiment_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """
    Get top predicted associations as a subgraph for visualization.
    """
    service = PredictionService(db)
    subgraph = await service.get_top_predictions(experiment_id, limit=limit)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=subgraph,
    )
