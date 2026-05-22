"""Prediction database model."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Prediction(Base):
    """Prediction model for storing prediction history."""
    
    __tablename__ = "predictions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Prediction type: 'single', 'batch', 'recommendation'
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Associated experiment/model
    experiment_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("experiments.id", ondelete="SET NULL"), nullable=True)
    
    # User who made the prediction
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Input data (drug name/ID, disease name/ID, etc.)
    input_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Prediction result (score, probability, recommended items, etc.)
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Task tracking
    task_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, running, completed, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    experiment = relationship("Experiment")
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self) -> str:
        return f"<Prediction {self.id} (type={self.type}, status={self.status})>"
