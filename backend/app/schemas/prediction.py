from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class PredictionRequest(BaseModel):
    drug_id: str = Field(..., description="ID of the drug")
    disease_id: str = Field(..., description="ID of the disease")
    model_id: Optional[int] = Field(None, description="ID of the experiment/model to use. If None, uses active model.")

class PredictionResponse(BaseModel):
    drug_id: str
    disease_id: str
    drug_name: Optional[str] = None
    disease_name: Optional[str] = None
    probability: float = Field(..., description="Predicted probability of association")
    label: int = Field(..., description="Predicted label (0 or 1)")
    model_id: int
    model_name: str

class BatchPredictionRequest(BaseModel):
    dataset_id: Optional[int] = Field(None, description="ID of the dataset containing pairs to predict. If provided, pairs_file is ignored.")
    model_id: Optional[int] = Field(None, description="ID of the experiment/model to use. If None, uses active model.")

class BatchPredictionResponse(BaseModel):
    task_id: str = Field(..., description="ID of the async task")
    message: str = "Batch prediction task started"

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: float
    message: Optional[str] = None
    result: Optional[Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============== Recommendation Schemas ==============


class DrugRecommendationRequest(BaseModel):
    """Request schema for disease → drug recommendation."""

    disease_id: str = Field(..., description="Disease ID to recommend drugs for")
    top_k: int = Field(
        10,
        ge=1,
        le=200,
        description="Number of top drugs to return",
    )
    model_id: Optional[int] = Field(
        None,
        description="ID of the experiment/model to use. If None, uses active model.",
    )


class DrugRecommendationItem(BaseModel):
    """Single recommended drug for a given disease."""

    drug_id: str
    probability: float = Field(..., description="Predicted association probability")
    label: Optional[int] = Field(
        None, description="Predicted label (0 or 1) if available"
    )
    drug_name: Optional[str] = None


class DrugRecommendationResponse(BaseModel):
    """Response schema for disease → drug recommendation."""

    disease_id: str
    disease_name: Optional[str] = None
    model_id: int
    model_name: str
    items: List[DrugRecommendationItem]


class DiseaseRecommendationRequest(BaseModel):
    """Request schema for drug → disease recommendation."""

    drug_id: str = Field(..., description="Drug ID to recommend diseases for")
    top_k: int = Field(
        10,
        ge=1,
        le=200,
        description="Number of top diseases to return",
    )
    model_id: Optional[int] = Field(
        None,
        description="ID of the experiment/model to use. If None, uses active model.",
    )


class DiseaseRecommendationItem(BaseModel):
    """Single recommended disease for a given drug."""

    disease_id: str
    probability: float = Field(..., description="Predicted association probability")
    label: Optional[int] = Field(
        None, description="Predicted label (0 or 1) if available"
    )
    disease_name: Optional[str] = None


class DiseaseRecommendationResponse(BaseModel):
    """Response schema for drug → disease recommendation."""

    drug_id: str
    drug_name: Optional[str] = None
    model_id: int
    model_name: str
    items: List[DiseaseRecommendationItem]


# ============== History Schemas ==============


class PredictionHistoryItem(BaseModel):
    """Single prediction history record."""

    id: int
    type: str = Field(..., description="Prediction type: single, batch, recommendation")
    experiment_id: Optional[int] = None
    user_id: Optional[int] = None
    task_id: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    input_data: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class PredictionHistoryResponse(BaseModel):
    """Paginated prediction history list."""

    items: List[PredictionHistoryItem]
    total: int
    page: int
    page_size: int
    pages: int

