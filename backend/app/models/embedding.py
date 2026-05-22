"""Embedding database model."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Embedding(Base):
    """Embedding model for storing trained embeddings."""
    
    __tablename__ = "embeddings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Source graph
    graph_id: Mapped[int] = mapped_column(Integer, ForeignKey("graphs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Algorithm type: 'node2vec' or 'gcn'
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Embedding dimension
    embedding_dim: Mapped[int] = mapped_column(Integer, nullable=False, default=64)
    
    # Common training parameters
    epochs: Mapped[int] = mapped_column(Integer, default=100)
    learning_rate: Mapped[float] = mapped_column(Float, default=0.01)
    random_seed: Mapped[int] = mapped_column(Integer, default=42)
    
    # Node2Vec specific parameters (stored as JSON)
    # walk_length, num_walks, p, q, window_size
    node2vec_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # GCN specific parameters (stored as JSON)
    # hidden_channels, num_layers, dropout
    gcn_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Training results
    training_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    val_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    training_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Training history (loss per epoch)
    training_history: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # File paths
    embedding_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    model_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, running, completed, failed
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Task tracking (for Celery)
    task_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Metadata
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    graph = relationship("Graph", foreign_keys=[graph_id])
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self) -> str:
        return f"<Embedding {self.name} (id={self.id}, algorithm={self.algorithm})>"
