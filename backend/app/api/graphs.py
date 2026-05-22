"""Graph API endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.models.user import User
from app.schemas.graph import (
    GraphBuildRequest,
    GraphResponse,
    GraphListResponse,
    GraphSummary,
    NodeIndexMapping,
    GraphUpdate,
    SubgraphResponse,
)
from app.schemas.response import ResponseModel
from app.services.graph import GraphService


router = APIRouter(prefix="/graphs", tags=["Graphs"])


@router.post("/build", response_model=ResponseModel[GraphResponse])
async def build_graph(
    request: GraphBuildRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Build a bipartite graph from a dataset.
    
    This endpoint constructs a drug-disease bipartite graph with:
    - Node index mappings (drug and disease nodes)
    - Edge index (connections between drugs and diseases)
    - Train/val/test split masks
    - Negative sampling (if configured)
    
    The graph artifacts are saved to disk for use in subsequent
    embedding and training tasks.
    """
    service = GraphService(db)
    user_id = current_user.id if current_user else None
    
    graph = await service.build_graph(request, user_id)
    
    return ResponseModel(
        code=200,
        message="Graph built successfully" if graph.is_built else f"Graph build failed: {graph.build_error}",
        data=GraphResponse.model_validate(graph),
    )


@router.get("", response_model=ResponseModel[GraphListResponse])
async def list_graphs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    keyword: Optional[str] = Query(default=None),
    dataset_id: Optional[int] = Query(default=None),
    is_built: Optional[bool] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """List graphs with optional filtering and pagination."""
    service = GraphService(db)
    
    result = await service.list_graphs(
        page=page,
        page_size=page_size,
        keyword=keyword,
        dataset_id=dataset_id,
        is_built=is_built,
    )
    
    return ResponseModel(
        code=200,
        message="Success",
        data=result,
    )


@router.get("/{graph_id}", response_model=ResponseModel[GraphResponse])
async def get_graph(
    graph_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get graph details by ID."""
    service = GraphService(db)
    graph = await service.get_graph_or_404(graph_id)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=GraphResponse.model_validate(graph),
    )


@router.get("/{graph_id}/summary", response_model=ResponseModel[GraphSummary])
async def get_graph_summary(
    graph_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed summary of a graph.
    
    Returns comprehensive statistics including:
    - Node counts (drugs, diseases, total)
    - Edge counts (positive, negative, total)
    - Split statistics (train/val/test)
    - Build parameters
    """
    service = GraphService(db)
    summary = await service.get_graph_summary(graph_id)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=summary,
    )


@router.get("/{graph_id}/node-index", response_model=ResponseModel[NodeIndexMapping])
async def get_node_index(
    graph_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get node index mapping for a graph.
    
    Returns mappings between:
    - Drug IDs and their node indices
    - Disease IDs and their node indices
    - Node indices back to original IDs
    """
    service = GraphService(db)
    node_index = await service.get_node_index(graph_id)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=node_index,
    )


@router.put("/{graph_id}", response_model=ResponseModel[GraphResponse])
async def update_graph(
    graph_id: int,
    update_data: GraphUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update graph metadata (name, description)."""
    service = GraphService(db)
    graph = await service.update_graph(graph_id, update_data)
    
    return ResponseModel(
        code=200,
        message="Graph updated successfully",
        data=GraphResponse.model_validate(graph),
    )


@router.delete("/{graph_id}", response_model=ResponseModel)
async def delete_graph(
    graph_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a graph and its associated files."""
    service = GraphService(db)
    await service.delete_graph(graph_id)
    
    return ResponseModel(
        code=200,
        message="Graph deleted successfully",
    )


@router.get("/dataset/{dataset_id}", response_model=ResponseModel[list[GraphResponse]])
async def get_graphs_by_dataset(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all graphs built from a specific dataset."""
    service = GraphService(db)
    graphs = await service.get_graphs_by_dataset(dataset_id)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=[GraphResponse.model_validate(g) for g in graphs],
    )


@router.get("/{graph_id}/subgraph", response_model=ResponseModel[SubgraphResponse])
async def get_subgraph(
    graph_id: int,
    limit: int = Query(default=100, ge=1, le=500),
    node_id: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a subgraph for visualization.
    
    - If `node_id` is provided, returns the local neighborhood of that node.
    - Otherwise, returns a random sample of positive edges.
    """
    service = GraphService(db)
    subgraph = await service.get_subgraph(graph_id, limit=limit, node_id=node_id)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=subgraph,
    )
