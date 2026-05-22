"""Embedding service for training and managing embeddings."""
import os
import json
import math
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from fastapi import HTTPException
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.embedding import Embedding
from app.models.graph import Graph
from app.schemas.embedding import (
    EmbeddingTrainRequest,
    EmbeddingResponse,
    EmbeddingListResponse,
    EmbeddingDetail,
    EmbeddingUpdate,
    TrainingHistory,
    TrainingProgress,
)
from app.algorithms.embeddings import Node2VecTrainer
from app.algorithms.gnn import GCNTrainer


class EmbeddingService:
    """Service class for embedding operations."""
    
    EMBEDDING_DIR = "embeddings"
    GRAPH_DIR = "data/graphs"
    # Shared executor to avoid creating threads per-request/service instance
    _EXECUTOR = ThreadPoolExecutor(max_workers=2)
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_embedding(
        self,
        request: EmbeddingTrainRequest,
        user_id: Optional[int] = None,
    ) -> Embedding:
        """Create a new embedding training job."""
        # Validate graph exists and is built
        graph = await self._get_graph_or_404(request.graph_id)
        if not graph.is_built:
            raise HTTPException(
                status_code=400,
                detail="Graph has not been built successfully"
            )
        
        # Validate algorithm-specific parameters
        node2vec_params = None
        gcn_params = None
        
        if request.algorithm == "node2vec":
            if request.node2vec_params:
                node2vec_params = request.node2vec_params.model_dump()
            else:
                # Use defaults
                node2vec_params = {
                    "walk_length": 80,
                    "num_walks": 10,
                    "p": 1.0,
                    "q": 1.0,
                    "window_size": 5,
                }
        elif request.algorithm == "gcn":
            if request.gcn_params:
                gcn_params = request.gcn_params.model_dump()
            else:
                # Use defaults
                gcn_params = {
                    "hidden_channels": 64,
                    "num_layers": 2,
                    "dropout": 0.5,
                }
        
        # Create embedding record
        embedding = Embedding(
            name=request.name,
            description=request.description,
            graph_id=request.graph_id,
            algorithm=request.algorithm,
            embedding_dim=request.embedding_dim,
            epochs=request.epochs,
            learning_rate=request.learning_rate,
            random_seed=request.random_seed,
            node2vec_params=node2vec_params,
            gcn_params=gcn_params,
            status="pending",
            progress=0,
            created_by=user_id,
        )
        
        self.db.add(embedding)
        await self.db.commit()
        await self.db.refresh(embedding)
        
        return embedding
    
    async def start_training(
        self,
        embedding_id: int,
        progress_callback: Optional[Callable[[int, int, float, Optional[float]], None]] = None,
    ) -> Optional[Embedding]:
        """Start training for an embedding."""
        embedding = await self.get_embedding_or_404(embedding_id)
        
        if embedding.status == "running":
            raise HTTPException(status_code=400, detail="Training is already running")
        
        if embedding.status == "completed":
            raise HTTPException(status_code=400, detail="Training is already completed")
        
        # Update status
        embedding.status = "running"
        embedding.started_at = datetime.utcnow()
        embedding.progress = 0
        await self.db.commit()
        
        try:
            # Run training in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._EXECUTOR,
                self._train_embedding_sync,
                embedding.id,
                embedding.graph_id,
                embedding.algorithm,
                embedding.embedding_dim,
                embedding.epochs,
                embedding.learning_rate,
                embedding.random_seed,
                embedding.node2vec_params,
                embedding.gcn_params,
            )
            
            embeddings_array, metadata, history = result
            
            # Re-fetch in case the record was deleted while training was running
            embedding = await self.get_embedding(embedding_id)
            if not embedding:
                return None
            
            # Create embedding directory
            embedding_dir = os.path.join(self.EMBEDDING_DIR, str(embedding.id))
            os.makedirs(embedding_dir, exist_ok=True)
            
            # Save embeddings
            embedding_path = os.path.join(embedding_dir, f"{embedding.algorithm}.npy")
            np.save(embedding_path, embeddings_array)
            
            # Save model metadata
            model_path = os.path.join(embedding_dir, f"{embedding.algorithm}_model.json")
            with open(model_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            # Update embedding record
            embedding.embedding_path = embedding_path
            embedding.model_path = model_path
            embedding.status = "completed"
            embedding.progress = 100
            embedding.completed_at = datetime.utcnow()
            embedding.training_loss = metadata.get("final_train_loss")
            embedding.val_loss = metadata.get("final_val_loss")
            embedding.training_time_seconds = metadata.get("training_time_seconds")
            embedding.training_history = history
        except asyncio.CancelledError:
            # If the HTTP request is cancelled (client timeout/disconnect),
            # we must not leave the record stuck at "running".
            embedding.status = "failed"
            embedding.error_message = "Training cancelled"
            await self.db.commit()
            await self.db.refresh(embedding)
            raise
        except Exception as e:
            embedding.status = "failed"
            embedding.error_message = str(e)
        
        await self.db.commit()
        await self.db.refresh(embedding)
        return embedding
    
    def _train_embedding_sync(
        self,
        embedding_id: int,
        graph_id: int,
        algorithm: str,
        embedding_dim: int,
        epochs: int,
        learning_rate: float,
        random_seed: int,
        node2vec_params: Optional[Dict],
        gcn_params: Optional[Dict],
    ) -> tuple:
        """Synchronous training function to run in executor."""
        # Load graph data
        graph_dir = os.path.join(self.GRAPH_DIR, str(graph_id))
        
        # Load node index
        node_index_path = os.path.join(graph_dir, "node_index.json")
        with open(node_index_path, "r") as f:
            node_index = json.load(f)
        
        # Load edges
        edge_index = np.load(os.path.join(graph_dir, "edge_index.npy"))
        train_edges = np.load(os.path.join(graph_dir, "train_edges.npy"))
        val_edges = np.load(os.path.join(graph_dir, "val_edges.npy"))
        
        # Create trainer based on algorithm
        if algorithm == "node2vec":
            params = node2vec_params or {}
            trainer = Node2VecTrainer(
                embedding_dim=embedding_dim,
                epochs=epochs,
                learning_rate=learning_rate,
                random_seed=random_seed,
                walk_length=params.get("walk_length", 80),
                num_walks=params.get("num_walks", 10),
                p=params.get("p", 1.0),
                q=params.get("q", 1.0),
                window_size=params.get("window_size", 5),
            )
        elif algorithm == "gcn":
            params = gcn_params or {}
            trainer = GCNTrainer(
                embedding_dim=embedding_dim,
                epochs=epochs,
                learning_rate=learning_rate,
                random_seed=random_seed,
                hidden_channels=params.get("hidden_channels", 64),
                num_layers=params.get("num_layers", 2),
                dropout=params.get("dropout", 0.5),
            )
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        # Train
        embeddings, metadata = trainer.train(node_index, edge_index, train_edges, val_edges)
        history = trainer.get_history()
        
        return embeddings, metadata, history
    
    async def _get_graph_or_404(self, graph_id: int) -> Graph:
        """Get graph by ID or raise 404."""
        result = await self.db.execute(
            select(Graph).where(Graph.id == graph_id)
        )
        graph = result.scalar_one_or_none()
        if not graph:
            raise HTTPException(status_code=404, detail="Graph not found")
        return graph
    
    async def get_embedding(self, embedding_id: int) -> Optional[Embedding]:
        """Get embedding by ID."""
        result = await self.db.execute(
            select(Embedding).where(Embedding.id == embedding_id)
        )
        return result.scalar_one_or_none()
    
    async def get_embedding_or_404(self, embedding_id: int) -> Embedding:
        """Get embedding by ID or raise 404."""
        embedding = await self.get_embedding(embedding_id)
        if not embedding:
            raise HTTPException(status_code=404, detail="Embedding not found")
        return embedding
    
    async def list_embeddings(
        self,
        page: int = 1,
        page_size: int = 10,
        keyword: Optional[str] = None,
        graph_id: Optional[int] = None,
        algorithm: Optional[str] = None,
        status: Optional[str] = None,
    ) -> EmbeddingListResponse:
        """List embeddings with filtering and pagination."""
        # Build query
        query = select(Embedding)
        conditions = []
        
        if keyword:
            conditions.append(
                or_(
                    Embedding.name.ilike(f"%{keyword}%"),
                    Embedding.description.ilike(f"%{keyword}%"),
                )
            )
        
        if graph_id is not None:
            conditions.append(Embedding.graph_id == graph_id)
        
        if algorithm:
            conditions.append(Embedding.algorithm == algorithm)
        
        if status:
            conditions.append(Embedding.status == status)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(Embedding)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Embedding.created_at.desc()).offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        embeddings = result.scalars().all()
        
        pages = math.ceil(total / page_size) if page_size > 0 else 0
        
        return EmbeddingListResponse(
            items=[EmbeddingResponse.model_validate(e) for e in embeddings],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
    
    async def get_embedding_detail(self, embedding_id: int) -> EmbeddingDetail:
        """Get detailed embedding information."""
        embedding = await self.get_embedding_or_404(embedding_id)
        graph = await self._get_graph_or_404(embedding.graph_id)
        
        # Parse training history
        training_history = None
        if embedding.training_history:
            history = embedding.training_history
            training_history = TrainingHistory(
                epochs=history.get("epochs", []),
                train_losses=history.get("train_losses", []),
                val_losses=history.get("val_losses"),
            )
        
        return EmbeddingDetail(
            id=embedding.id,
            name=embedding.name,
            description=embedding.description,
            graph_id=embedding.graph_id,
            graph_name=graph.name,
            algorithm=embedding.algorithm,
            embedding_dim=embedding.embedding_dim,
            epochs=embedding.epochs,
            learning_rate=embedding.learning_rate,
            random_seed=embedding.random_seed,
            node2vec_params=embedding.node2vec_params,
            gcn_params=embedding.gcn_params,
            status=embedding.status,
            progress=embedding.progress,
            training_loss=embedding.training_loss,
            val_loss=embedding.val_loss,
            training_time_seconds=embedding.training_time_seconds,
            training_history=training_history,
            num_nodes=graph.num_total_nodes,
            num_edges=graph.num_edges,
            created_at=embedding.created_at,
            updated_at=embedding.updated_at,
        )
    
    async def get_training_progress(self, embedding_id: int) -> TrainingProgress:
        """Get current training progress."""
        embedding = await self.get_embedding_or_404(embedding_id)
        
        current_epoch = None
        current_loss = None
        current_val_loss = None
        
        if embedding.training_history:
            history = embedding.training_history
            epochs = history.get("epochs", [])
            train_losses = history.get("train_losses", [])
            val_losses = history.get("val_losses", [])
            
            if epochs:
                current_epoch = epochs[-1]
            if train_losses:
                current_loss = train_losses[-1]
            if val_losses:
                current_val_loss = val_losses[-1]
        
        return TrainingProgress(
            status=embedding.status,
            progress=embedding.progress,
            current_epoch=current_epoch,
            current_loss=current_loss,
            current_val_loss=current_val_loss,
        )
    
    async def get_training_history(self, embedding_id: int) -> TrainingHistory:
        """Get training history with loss curves."""
        embedding = await self.get_embedding_or_404(embedding_id)
        
        if not embedding.training_history:
            return TrainingHistory(epochs=[], train_losses=[], val_losses=[])
        
        history = embedding.training_history
        return TrainingHistory(
            epochs=history.get("epochs", []),
            train_losses=history.get("train_losses", []),
            val_losses=history.get("val_losses"),
        )
    
    async def update_embedding(
        self,
        embedding_id: int,
        update_data: EmbeddingUpdate,
    ) -> Embedding:
        """Update embedding metadata."""
        embedding = await self.get_embedding_or_404(embedding_id)
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(embedding, key, value)
        
        await self.db.commit()
        await self.db.refresh(embedding)
        
        return embedding
    
    async def delete_embedding(self, embedding_id: int) -> bool:
        """Delete embedding and associated files. Allowed even when status is 'running' (e.g. stuck tasks)."""
        embedding = await self.get_embedding_or_404(embedding_id)
        
        # Delete embedding directory
        embedding_dir = os.path.join(self.EMBEDDING_DIR, str(embedding.id))
        if os.path.exists(embedding_dir):
            import shutil
            try:
                shutil.rmtree(embedding_dir)
            except OSError:
                pass
        
        # Delete from database
        await self.db.delete(embedding)
        await self.db.commit()
        
        return True
    
    async def get_embeddings_by_graph(self, graph_id: int) -> List[Embedding]:
        """Get all embeddings for a graph."""
        result = await self.db.execute(
            select(Embedding)
            .where(Embedding.graph_id == graph_id)
            .order_by(Embedding.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def load_embeddings(self, embedding_id: int) -> np.ndarray:
        """Load embedding vectors from file."""
        embedding = await self.get_embedding_or_404(embedding_id)
        
        if embedding.status != "completed":
            raise HTTPException(
                status_code=400,
                detail="Embedding training has not been completed"
            )
        
        if not embedding.embedding_path or not os.path.exists(embedding.embedding_path):
            raise HTTPException(
                status_code=404,
                detail="Embedding file not found"
            )
        
        return np.load(embedding.embedding_path)
