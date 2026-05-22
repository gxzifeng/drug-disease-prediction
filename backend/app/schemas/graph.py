"""Graph Pydantic schemas."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============== Graph Build Request ==============

class GraphBuildRequest(BaseModel):
    """Request schema for building a graph from dataset."""
    dataset_id: int = Field(..., description="Source dataset ID")
    name: str = Field(..., min_length=1, max_length=200, description="Graph name")
    description: Optional[str] = Field(None, description="Graph description")
    negative_sample_ratio: float = Field(default=1.0, ge=0.1, le=10.0, description="Ratio of negative samples to positive samples")
    train_ratio: float = Field(default=0.7, ge=0.1, le=0.9, description="Training set ratio")
    val_ratio: float = Field(default=0.15, ge=0.05, le=0.4, description="Validation set ratio")
    test_ratio: float = Field(default=0.15, ge=0.05, le=0.4, description="Test set ratio")
    random_seed: int = Field(default=42, ge=0, description="Random seed for reproducibility")


# ============== Graph Response Schemas ==============

class GraphBase(BaseModel):
    """Base schema for graph."""
    name: str
    description: Optional[str] = None
    dataset_id: int
    negative_sample_ratio: float
    train_ratio: float
    val_ratio: float
    test_ratio: float
    random_seed: int


class GraphResponse(GraphBase):
    """Response schema for graph."""
    id: int
    num_drug_nodes: int
    num_disease_nodes: int
    num_total_nodes: int
    num_edges: int
    num_positive_edges: int
    num_negative_edges: int
    num_train_edges: int
    num_val_edges: int
    num_test_edges: int
    is_built: bool
    build_error: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GraphListResponse(BaseModel):
    """Response schema for paginated graph list."""
    items: List[GraphResponse]
    total: int
    page: int
    page_size: int
    pages: int


class GraphSummary(BaseModel):
    """Graph summary statistics."""
    # Basic info
    id: int
    name: str
    dataset_id: int
    dataset_name: str
    
    # Node statistics
    num_drug_nodes: int
    num_disease_nodes: int
    num_total_nodes: int
    
    # Edge statistics
    num_edges: int
    num_positive_edges: int
    num_negative_edges: int
    positive_ratio: float
    
    # Split statistics
    num_train_edges: int
    num_val_edges: int
    num_test_edges: int
    train_ratio_actual: float
    val_ratio_actual: float
    test_ratio_actual: float
    
    # Build parameters
    negative_sample_ratio: float
    random_seed: int
    
    # Status
    is_built: bool
    created_at: datetime


class NodeIndexMapping(BaseModel):
    """Node index mapping response."""
    drug_to_idx: Dict[str, int]
    disease_to_idx: Dict[str, int]
    idx_to_drug: Dict[int, str]
    idx_to_disease: Dict[int, str]


class GraphNode(BaseModel):
    """Node in a subgraph."""
    id: str
    name: str
    type: str  # 'drug' or 'disease'


class GraphEdge(BaseModel):
    """Edge in a subgraph."""
    source: str
    target: str
    label: int  # 1 for positive, 0 for negative
    type: str = "original"  # 'original' or 'predicted'


class SubgraphResponse(BaseModel):
    """Response schema for a subgraph."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class GraphUpdate(BaseModel):
    """Schema for updating graph metadata."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


# ============== Filter Schemas ==============

class GraphFilter(BaseModel):
    """Schema for filtering graphs."""
    keyword: Optional[str] = None
    dataset_id: Optional[int] = None
    is_built: Optional[bool] = None
