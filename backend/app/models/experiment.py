"""Experiment database model for classifier training."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Experiment(Base):
    """Experiment model for storing ML classifier experiments."""
    
    __tablename__ = "experiments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Source embedding
    embedding_id: Mapped[int] = mapped_column(Integer, ForeignKey("embeddings.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Classifier type: 'random_forest', 'xgboost', 'svm'
    classifier: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Feature combination method: 'concat', 'hadamard', 'l1', 'l2', 'average'
    feature_method: Mapped[str] = mapped_column(String(50), nullable=False, default="concat")
    
    # Training parameters
    random_seed: Mapped[int] = mapped_column(Integer, default=42)
    test_size: Mapped[float] = mapped_column(Float, default=0.2)
    k_fold: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)  # None means no k-fold
    
    # Classifier specific parameters (stored as JSON)
    # RF: n_estimators, max_depth, min_samples_split, min_samples_leaf
    # XGBoost: n_estimators, max_depth, learning_rate, subsample
    # SVM: C, kernel, gamma
    classifier_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Evaluation metrics
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precision: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recall: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    f1_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    auc_roc: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    auc_pr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # K-fold metrics (if enabled)
    kfold_metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Feature importance
    feature_importance: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Confusion matrix [TN, FP, FN, TP]
    confusion_matrix: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Training metadata
    training_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    num_train_samples: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    num_test_samples: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    num_features: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # File paths
    model_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, running, completed, failed
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Task tracking (for Celery)
    task_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Is this the default/active model for predictions?
    is_active: Mapped[bool] = mapped_column(default=False)
    
    # Metadata
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    embedding = relationship("Embedding", foreign_keys=[embedding_id])
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self) -> str:
        return f"<Experiment {self.name} (id={self.id}, classifier={self.classifier})>"
