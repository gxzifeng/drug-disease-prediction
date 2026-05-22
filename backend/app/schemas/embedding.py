"""Embedding Pydantic schemas."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============== Node2Vec Parameters ==============

class Node2VecParams(BaseModel):
    """Node2Vec algorithm parameters."""
    walk_length: int = Field(default=80, ge=10, le=200, description="Random walk length")
    num_walks: int = Field(default=10, ge=1, le=50, description="Number of walks per node")
    p: float = Field(default=1.0, ge=0.1, le=10.0, description="Return parameter")
    q: float = Field(default=1.0, ge=0.1, le=10.0, description="In-out parameter")
    window_size: int = Field(default=5, ge=2, le=20, description="Skip-gram window size")


# ============== GCN Parameters ==============

class GCNParams(BaseModel):
    """GCN algorithm parameters."""
    hidden_channels: int = Field(default=64, ge=16, le=512, description="Hidden layer dimension")
    num_layers: int = Field(default=2, ge=1, le=5, description="Number of GCN layers")
    dropout: float = Field(default=0.5, ge=0.0, le=0.9, description="Dropout rate")


# ============== Training Request ==============

class EmbeddingTrainRequest(BaseModel):
    """Request schema for training embeddings."""
    graph_id: int = Field(..., description="Source graph ID")
    name: str = Field(..., min_length=1, max_length=200, description="Embedding name")
    description: Optional[str] = Field(None, description="Embedding description")
    algorithm: str = Field(..., pattern="^(node2vec|gcn)$", description="Algorithm type: node2vec or gcn")
    embedding_dim: int = Field(default=64, ge=16, le=512, description="Embedding dimension")
    epochs: int = Field(default=100, ge=1, le=1000, description="Number of training epochs")
    learning_rate: float = Field(default=0.01, gt=0, le=1.0, description="Learning rate")
    random_seed: int = Field(default=42, ge=0, description="Random seed for reproducibility")
    
    # Algorithm-specific parameters (only one should be provided)
    node2vec_params: Optional[Node2VecParams] = None
    gcn_params: Optional[GCNParams] = None


# ============== Response Schemas ==============

class EmbeddingBase(BaseModel):
    """Base schema for embedding."""
    name: str
    description: Optional[str] = None
    graph_id: int
    algorithm: str
    embedding_dim: int
    epochs: int
    learning_rate: float
    random_seed: int


class TrainingProgress(BaseModel):
    """Training progress information."""
    status: str
    progress: int
    current_epoch: Optional[int] = None
    current_loss: Optional[float] = None
    current_val_loss: Optional[float] = None


class TrainingHistory(BaseModel):
    """Training history with loss curves."""
    epochs: List[int]
    train_losses: List[float]
    val_losses: Optional[List[float]] = None


class EmbeddingResponse(EmbeddingBase):
    """Response schema for embedding."""
    id: int
    node2vec_params: Optional[Dict[str, Any]] = None
    gcn_params: Optional[Dict[str, Any]] = None
    training_loss: Optional[float] = None
    val_loss: Optional[float] = None
    training_time_seconds: Optional[float] = None
    training_history: Optional[Dict[str, Any]] = None
    embedding_path: Optional[str] = None
    model_path: Optional[str] = None
    status: str
    progress: int
    error_message: Optional[str] = None
    task_id: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EmbeddingListResponse(BaseModel):
    """Response schema for paginated embedding list."""
    items: List[EmbeddingResponse]
    total: int
    page: int
    page_size: int
    pages: int


class EmbeddingDetail(BaseModel):
    """Detailed embedding information."""
    id: int
    name: str
    description: Optional[str]
    graph_id: int
    graph_name: str
    algorithm: str
    embedding_dim: int
    epochs: int
    learning_rate: float
    random_seed: int
    node2vec_params: Optional[Dict[str, Any]] = None
    gcn_params: Optional[Dict[str, Any]] = None
    
    # Training results
    status: str
    progress: int
    training_loss: Optional[float] = None
    val_loss: Optional[float] = None
    training_time_seconds: Optional[float] = None
    
    # Training history
    training_history: Optional[TrainingHistory] = None
    
    # Statistics
    num_nodes: int
    num_edges: int
    
    created_at: datetime
    updated_at: datetime


class EmbeddingUpdate(BaseModel):
    """Schema for updating embedding metadata."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


# ============== Filter Schema ==============

class EmbeddingFilter(BaseModel):
    """Schema for filtering embeddings."""
    keyword: Optional[str] = None
    graph_id: Optional[int] = None
    algorithm: Optional[str] = None
    status: Optional[str] = None


# ============== Log Entry Schema ==============

class TrainingLogEntry(BaseModel):
    """Single training log entry."""
    timestamp: datetime
    epoch: int
    train_loss: float
    val_loss: Optional[float] = None
    message: Optional[str] = None
