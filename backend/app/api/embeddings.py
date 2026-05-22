"""Embedding API endpoints."""
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, AsyncSessionLocal
from app.core.deps import get_current_user, get_optional_user
from app.models.user import User
from app.schemas.embedding import (
    EmbeddingTrainRequest,
    EmbeddingResponse,
    EmbeddingListResponse,
    EmbeddingDetail,
    EmbeddingUpdate,
    TrainingProgress,
    TrainingHistory,
)
from app.schemas.response import ResponseModel
from app.services.embedding import EmbeddingService


router = APIRouter(prefix="/embeddings", tags=["Embeddings"])


@router.post("/train", response_model=ResponseModel[EmbeddingResponse])
async def create_and_train_embedding(
    request: EmbeddingTrainRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Create and start training an embedding.
    
    This endpoint creates an embedding training job and starts training in the background.
    Supported algorithms:
    - **node2vec**: Random walk based embedding using skip-gram
    - **gcn**: Graph Convolutional Network based embedding
    
    Training progress can be monitored via the progress endpoint.
    """
    service = EmbeddingService(db)
    user_id = current_user.id if current_user else None
    
    # Create embedding record
    embedding = await service.create_embedding(request, user_id)

    # Start training in background (so the HTTP request returns immediately)
    async def train_task(embedding_id: int):
        async with AsyncSessionLocal() as session:
            train_service = EmbeddingService(session)
            await train_service.start_training(embedding_id)

    background_tasks.add_task(train_task, embedding.id)
    
    return ResponseModel(
        code=200,
        message="Embedding created; training scheduled",
        data=EmbeddingResponse.model_validate(embedding),
    )


@router.post("", response_model=ResponseModel[EmbeddingResponse])
async def create_embedding(
    request: EmbeddingTrainRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Create an embedding training job without starting it.
    
    Use this endpoint to create the job first, then start training separately.
    """
    service = EmbeddingService(db)
    user_id = current_user.id if current_user else None
    
    embedding = await service.create_embedding(request, user_id)
    
    return ResponseModel(
        code=200,
        message="Embedding created successfully",
        data=EmbeddingResponse.model_validate(embedding),
    )


@router.post("/{embedding_id}/start", response_model=ResponseModel[EmbeddingResponse])
async def start_training(
    embedding_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start training for an existing embedding job."""
    # Validate access and embedding exists using current request session.
    service = EmbeddingService(db)
    embedding = await service.get_embedding_or_404(embedding_id)

    async def train_task(eid: int):
        async with AsyncSessionLocal() as session:
            train_service = EmbeddingService(session)
            await train_service.start_training(eid)

    background_tasks.add_task(train_task, embedding.id)
    
    return ResponseModel(
        code=200,
        message="Training scheduled",
        data=EmbeddingResponse.model_validate(embedding),
    )


@router.get("", response_model=ResponseModel[EmbeddingListResponse])
async def list_embeddings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    keyword: Optional[str] = Query(default=None),
    graph_id: Optional[int] = Query(default=None),
    algorithm: Optional[str] = Query(default=None, pattern="^(node2vec|gcn)$"),
    status: Optional[str] = Query(default=None, pattern="^(pending|running|completed|failed)$"),
    db: AsyncSession = Depends(get_db),
):
    """List embeddings with optional filtering and pagination."""
    service = EmbeddingService(db)
    
    result = await service.list_embeddings(
        page=page,
        page_size=page_size,
        keyword=keyword,
        graph_id=graph_id,
        algorithm=algorithm,
        status=status,
    )
    
    return ResponseModel(
        code=200,
        message="Success",
        data=result,
    )


@router.get("/{embedding_id}", response_model=ResponseModel[EmbeddingResponse])
async def get_embedding(
    embedding_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get embedding details by ID."""
    service = EmbeddingService(db)
    embedding = await service.get_embedding_or_404(embedding_id)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=EmbeddingResponse.model_validate(embedding),
    )


@router.get("/{embedding_id}/detail", response_model=ResponseModel[EmbeddingDetail])
async def get_embedding_detail(
    embedding_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed embedding information including graph info and training history.
    """
    service = EmbeddingService(db)
    detail = await service.get_embedding_detail(embedding_id)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=detail,
    )


@router.get("/{embedding_id}/progress", response_model=ResponseModel[TrainingProgress])
async def get_training_progress(
    embedding_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get current training progress."""
    service = EmbeddingService(db)
    progress = await service.get_training_progress(embedding_id)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=progress,
    )


@router.get("/{embedding_id}/history", response_model=ResponseModel[TrainingHistory])
async def get_training_history(
    embedding_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get training history with loss curves.
    
    Returns epoch-by-epoch training and validation losses for visualization.
    """
    service = EmbeddingService(db)
    history = await service.get_training_history(embedding_id)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=history,
    )


@router.put("/{embedding_id}", response_model=ResponseModel[EmbeddingResponse])
async def update_embedding(
    embedding_id: int,
    update_data: EmbeddingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update embedding metadata (name, description)."""
    service = EmbeddingService(db)
    embedding = await service.update_embedding(embedding_id, update_data)
    
    return ResponseModel(
        code=200,
        message="Embedding updated successfully",
        data=EmbeddingResponse.model_validate(embedding),
    )


@router.delete("/{embedding_id}", response_model=ResponseModel)
async def delete_embedding(
    embedding_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an embedding and its associated files."""
    service = EmbeddingService(db)
    await service.delete_embedding(embedding_id)
    
    return ResponseModel(
        code=200,
        message="Embedding deleted successfully",
    )


@router.get("/graph/{graph_id}", response_model=ResponseModel[List[EmbeddingResponse]])
async def get_embeddings_by_graph(
    graph_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all embeddings for a specific graph."""
    service = EmbeddingService(db)
    embeddings = await service.get_embeddings_by_graph(graph_id)
    
    return ResponseModel(
        code=200,
        message="Success",
        data=[EmbeddingResponse.model_validate(e) for e in embeddings],
    )
