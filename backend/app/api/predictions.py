"""Prediction API endpoints for drug-disease association predictions."""
from typing import Optional, List
import os
from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.models.user import User
from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    TaskStatusResponse,
    DrugRecommendationRequest,
    DrugRecommendationResponse,
    DiseaseRecommendationRequest,
    DiseaseRecommendationResponse,
    PredictionHistoryResponse,
)
from app.schemas.response import ResponseModel
from app.services.prediction import PredictionService
from app.tasks.prediction import run_batch_prediction
from app.core.config import settings

router = APIRouter(prefix="/predictions", tags=["Predictions"])

@router.post("/predict", response_model=ResponseModel[PredictionResponse])
async def predict_single(
    request: PredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Predict association for a single drug-disease pair."""
    service = PredictionService(db)
    result = await service.predict_single(request)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=result,
    )

@router.post("/batch", response_model=ResponseModel[BatchPredictionResponse])
async def predict_batch(
    request: BatchPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Start a batch prediction task."""
    user_id = current_user.id if current_user else None
    
    # Start celery task
    task = run_batch_prediction.delay(
        dataset_id=request.dataset_id,
        model_id=request.model_id,
        user_id=user_id
    )
    
    return ResponseModel(
        code=202,
        message="Batch prediction task started",
        data=BatchPredictionResponse(task_id=task.id),
    )

@router.get("/tasks/{task_id}", response_model=ResponseModel[TaskStatusResponse])
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Get status of a prediction or training task."""
    service = PredictionService(db)
    result = await service.get_task_status(task_id)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=TaskStatusResponse(**result),
    )

@router.get("/download/{filename}")
async def download_results(
    filename: str,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Download batch prediction results."""
    # Security check: ensure filename is just a filename
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
        
    filepath = os.path.join(settings.PREDICTION_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="text/csv"
    )


@router.post(
    "/drug-recommendation",
    response_model=ResponseModel[DrugRecommendationResponse],
    summary="Recommend drugs for a given disease",
)
async def recommend_drugs(
    request: DrugRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Recommend top-K drugs for a given disease.

    Uses the specified model (or the active model if not provided) to score
    all drug candidates and return the highest scoring ones.
    """
    service = PredictionService(db)
    user_id = current_user.id if current_user else None
    result = await service.recommend_drugs(
        disease_id=request.disease_id,
        top_k=request.top_k,
        model_id=request.model_id,
        user_id=user_id,
    )

    return ResponseModel(
        code=200,
        message="Success",
        data=DrugRecommendationResponse(**result),
    )


@router.post(
    "/disease-recommendation",
    response_model=ResponseModel[DiseaseRecommendationResponse],
    summary="Recommend diseases for a given drug",
)
async def recommend_diseases(
    request: DiseaseRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Recommend top-K diseases for a given drug.

    Uses the specified model (or the active model if not provided) to score
    all disease candidates and return the highest scoring ones.
    """
    service = PredictionService(db)
    user_id = current_user.id if current_user else None
    result = await service.recommend_diseases(
        drug_id=request.drug_id,
        top_k=request.top_k,
        model_id=request.model_id,
        user_id=user_id,
    )

    return ResponseModel(
        code=200,
        message="Success",
        data=DiseaseRecommendationResponse(**result),
    )


@router.get(
    "/history",
    response_model=ResponseModel[PredictionHistoryResponse],
    summary="Get prediction history",
)
async def get_prediction_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    type: Optional[str] = Query(
        default=None,
        description="Filter by prediction type: single, batch, recommendation",
    ),
    experiment_id: Optional[int] = Query(
        default=None,
        description="Filter by experiment/model ID",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get paginated prediction history for the current user.

    If the user is not authenticated, only global (user_id is null) records
    will be returned.
    """
    service = PredictionService(db)
    user_id = current_user.id if current_user else None
    result = await service.get_history(
        page=page,
        page_size=page_size,
        type=type,
        experiment_id=experiment_id,
        user_id=user_id,
    )

    return ResponseModel(
        code=200,
        message="Success",
        data=PredictionHistoryResponse(**result),
    )
