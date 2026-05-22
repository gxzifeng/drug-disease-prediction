"""Experiment Pydantic schemas."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============== Classifier Parameters ==============

class RandomForestParams(BaseModel):
    """Random Forest classifier parameters."""
    n_estimators: int = Field(default=100, ge=10, le=1000, description="Number of trees")
    max_depth: Optional[int] = Field(default=None, ge=1, le=50, description="Maximum depth of trees")
    min_samples_split: int = Field(default=2, ge=2, le=20, description="Minimum samples to split")
    min_samples_leaf: int = Field(default=1, ge=1, le=20, description="Minimum samples in leaf")
    class_weight: Optional[str] = Field(default="balanced", description="Class weight strategy")


class XGBoostParams(BaseModel):
    """XGBoost classifier parameters."""
    n_estimators: int = Field(default=100, ge=10, le=1000, description="Number of boosting rounds")
    max_depth: int = Field(default=6, ge=1, le=20, description="Maximum tree depth")
    learning_rate: float = Field(default=0.1, gt=0, le=1.0, description="Learning rate")
    subsample: float = Field(default=0.8, gt=0, le=1.0, description="Subsample ratio")
    colsample_bytree: float = Field(default=0.8, gt=0, le=1.0, description="Feature subsample ratio")
    scale_pos_weight: Optional[float] = Field(default=None, ge=0, description="Weight for positive class")


class SVMParams(BaseModel):
    """SVM classifier parameters."""
    C: float = Field(default=1.0, gt=0, le=100, description="Regularization parameter")
    kernel: str = Field(default="rbf", pattern="^(linear|rbf|poly|sigmoid)$", description="Kernel type")
    gamma: str = Field(default="scale", description="Kernel coefficient")
    probability: bool = Field(default=True, description="Enable probability estimates")


# ============== Training Request ==============

class ExperimentTrainRequest(BaseModel):
    """Request schema for training a classifier experiment."""
    embedding_id: int = Field(..., description="Source embedding ID")
    name: str = Field(..., min_length=1, max_length=200, description="Experiment name")
    description: Optional[str] = Field(None, description="Experiment description")
    classifier: str = Field(..., pattern="^(random_forest|xgboost|svm)$", description="Classifier type")
    feature_method: str = Field(
        default="concat", 
        pattern="^(concat|hadamard|l1|l2|average)$",
        description="Feature combination method"
    )
    random_seed: int = Field(default=42, ge=0, description="Random seed for reproducibility")
    test_size: float = Field(default=0.2, gt=0, lt=1.0, description="Test set proportion")
    k_fold: Optional[int] = Field(default=None, ge=2, le=10, description="K-fold cross validation (optional)")
    
    # Classifier-specific parameters (only one should be provided)
    random_forest_params: Optional[RandomForestParams] = None
    xgboost_params: Optional[XGBoostParams] = None
    svm_params: Optional[SVMParams] = None


# ============== Response Schemas ==============

class MetricsResponse(BaseModel):
    """Evaluation metrics response."""
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    auc_roc: Optional[float] = None
    auc_pr: Optional[float] = None


class ConfusionMatrixResponse(BaseModel):
    """Confusion matrix response."""
    tn: int
    fp: int
    fn: int
    tp: int


class KFoldMetrics(BaseModel):
    """K-fold cross validation metrics."""
    fold_metrics: List[MetricsResponse]
    mean_metrics: MetricsResponse
    std_metrics: MetricsResponse


class FeatureImportanceItem(BaseModel):
    """Single feature importance item."""
    feature_name: str
    importance: float


class ExperimentBase(BaseModel):
    """Base schema for experiment."""
    name: str
    description: Optional[str] = None
    embedding_id: int
    classifier: str
    feature_method: str
    random_seed: int
    test_size: float
    k_fold: Optional[int] = None


class ExperimentResponse(ExperimentBase):
    """Response schema for experiment."""
    id: int
    classifier_params: Optional[Dict[str, Any]] = None
    
    # Metrics
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    auc_roc: Optional[float] = None
    auc_pr: Optional[float] = None
    
    # K-fold metrics
    kfold_metrics: Optional[Dict[str, Any]] = None
    
    # Feature importance (top N)
    feature_importance: Optional[Dict[str, Any]] = None
    
    # Confusion matrix
    confusion_matrix: Optional[Dict[str, Any]] = None
    
    # Training metadata
    training_time_seconds: Optional[float] = None
    num_train_samples: Optional[int] = None
    num_test_samples: Optional[int] = None
    num_features: Optional[int] = None
    
    # Paths and status
    model_path: Optional[str] = None
    status: str
    progress: int
    error_message: Optional[str] = None
    task_id: Optional[str] = None
    is_active: bool = False
    
    # Timestamps
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ExperimentListResponse(BaseModel):
    """Response schema for paginated experiment list."""
    items: List[ExperimentResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ExperimentDetail(BaseModel):
    """Detailed experiment information."""
    id: int
    name: str
    description: Optional[str]
    embedding_id: int
    embedding_name: str
    graph_id: int
    graph_name: str
    classifier: str
    feature_method: str
    random_seed: int
    test_size: float
    k_fold: Optional[int] = None
    classifier_params: Optional[Dict[str, Any]] = None
    
    # Training results
    status: str
    progress: int
    
    # Metrics
    metrics: Optional[MetricsResponse] = None
    kfold_metrics: Optional[KFoldMetrics] = None
    
    # Feature importance
    feature_importance: Optional[List[FeatureImportanceItem]] = None
    
    # Confusion matrix
    confusion_matrix: Optional[ConfusionMatrixResponse] = None
    
    # Training metadata
    training_time_seconds: Optional[float] = None
    num_train_samples: Optional[int] = None
    num_test_samples: Optional[int] = None
    num_features: Optional[int] = None
    
    is_active: bool
    
    created_at: datetime
    updated_at: datetime


class ExperimentUpdate(BaseModel):
    """Schema for updating experiment metadata."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


# ============== Filter Schema ==============

class ExperimentFilter(BaseModel):
    """Schema for filtering experiments."""
    keyword: Optional[str] = None
    embedding_id: Optional[int] = None
    classifier: Optional[str] = None
    status: Optional[str] = None


# ============== Comparison Schema ==============

class ExperimentComparison(BaseModel):
    """Schema for comparing multiple experiments."""
    experiments: List[ExperimentResponse]
    best_by_auc_roc: Optional[int] = None
    best_by_f1: Optional[int] = None
