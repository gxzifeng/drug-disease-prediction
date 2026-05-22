"""Experiment service for training and managing classifier experiments."""
import os
import json
import math
import asyncio
import pickle
from datetime import datetime
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from fastapi import HTTPException
from sqlalchemy import select, func, or_, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.experiment import Experiment
from app.models.embedding import Embedding
from app.models.graph import Graph
from app.schemas.experiment import (
    ExperimentTrainRequest,
    ExperimentResponse,
    ExperimentListResponse,
    ExperimentDetail,
    ExperimentUpdate,
    MetricsResponse,
    KFoldMetrics,
    ConfusionMatrixResponse,
    FeatureImportanceItem,
)
from app.algorithms.classifiers import (
    BaseClassifier,
    FeatureCombiner,
    RandomForestClassifier,
    XGBoostClassifier,
    SVMClassifier,
)


class ExperimentService:
    """Service class for experiment operations."""
    
    MODEL_DIR = "models/experiments"
    EMBEDDING_DIR = "embeddings"
    GRAPH_DIR = "data/graphs"
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    async def create_experiment(
        self,
        request: ExperimentTrainRequest,
        user_id: Optional[int] = None,
    ) -> Experiment:
        """Create a new experiment."""
        # Validate embedding exists and is completed
        embedding = await self._get_embedding_or_404(request.embedding_id)
        if embedding.status != "completed":
            raise HTTPException(
                status_code=400,
                detail="Embedding training has not been completed"
            )
        
        # Prepare classifier parameters
        classifier_params = None
        if request.classifier == "random_forest":
            if request.random_forest_params:
                classifier_params = request.random_forest_params.model_dump()
            else:
                classifier_params = {
                    "n_estimators": 100,
                    "max_depth": None,
                    "min_samples_split": 2,
                    "min_samples_leaf": 1,
                    "class_weight": "balanced",
                }
        elif request.classifier == "xgboost":
            if request.xgboost_params:
                classifier_params = request.xgboost_params.model_dump()
            else:
                classifier_params = {
                    "n_estimators": 100,
                    "max_depth": 6,
                    "learning_rate": 0.1,
                    "subsample": 0.8,
                    "colsample_bytree": 0.8,
                    "scale_pos_weight": None,
                }
        elif request.classifier == "svm":
            if request.svm_params:
                classifier_params = request.svm_params.model_dump()
            else:
                classifier_params = {
                    "C": 1.0,
                    "kernel": "rbf",
                    "gamma": "scale",
                    "probability": True,
                    "class_weight": "balanced",
                }
        
        # Create experiment record
        experiment = Experiment(
            name=request.name,
            description=request.description,
            embedding_id=request.embedding_id,
            classifier=request.classifier,
            feature_method=request.feature_method,
            random_seed=request.random_seed,
            test_size=request.test_size,
            k_fold=request.k_fold,
            classifier_params=classifier_params,
            status="pending",
            progress=0,
            created_by=user_id,
        )
        
        self.db.add(experiment)
        await self.db.commit()
        await self.db.refresh(experiment)
        
        return experiment
    
    async def start_training(self, experiment_id: int) -> Experiment:
        """Start training for an experiment."""
        experiment = await self.get_experiment_or_404(experiment_id)
        
        if experiment.status == "running":
            raise HTTPException(status_code=400, detail="Training is already running")
        
        if experiment.status == "completed":
            raise HTTPException(status_code=400, detail="Training is already completed")
        
        # Get embedding
        embedding = await self._get_embedding_or_404(experiment.embedding_id)
        
        # Update status
        experiment.status = "running"
        experiment.started_at = datetime.utcnow()
        experiment.progress = 0
        await self.db.commit()
        
        try:
            # Run training in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor,
                self._train_experiment_sync,
                experiment.id,
                embedding.id,
                embedding.graph_id,
                embedding.embedding_path,
                experiment.classifier,
                experiment.feature_method,
                experiment.random_seed,
                experiment.test_size,
                experiment.k_fold,
                experiment.classifier_params,
            )
            
            metrics, model_path = result
            
            # Update experiment record
            experiment.accuracy = metrics.get("accuracy")
            experiment.precision = metrics.get("precision")
            experiment.recall = metrics.get("recall")
            experiment.f1_score = metrics.get("f1_score")
            experiment.auc_roc = metrics.get("auc_roc")
            experiment.auc_pr = metrics.get("auc_pr")
            experiment.confusion_matrix = metrics.get("confusion_matrix")
            experiment.feature_importance = {"importances": metrics.get("feature_importance", [])}
            experiment.kfold_metrics = metrics.get("kfold_metrics")
            experiment.training_time_seconds = metrics.get("training_time_seconds")
            experiment.num_train_samples = metrics.get("num_train_samples")
            experiment.num_test_samples = metrics.get("num_test_samples")
            experiment.num_features = metrics.get("num_features")
            experiment.model_path = model_path
            experiment.status = "completed"
            experiment.progress = 100
            experiment.completed_at = datetime.utcnow()
            
        except Exception as e:
            experiment.status = "failed"
            experiment.error_message = str(e)
        
        await self.db.commit()
        await self.db.refresh(experiment)
        
        return experiment
    
    def _train_experiment_sync(
        self,
        experiment_id: int,
        embedding_id: int,
        graph_id: int,
        embedding_path: str,
        classifier_type: str,
        feature_method: str,
        random_seed: int,
        test_size: float,
        k_fold: Optional[int],
        classifier_params: Optional[Dict],
    ) -> tuple:
        """Synchronous training function to run in executor."""
        # Load embeddings
        embeddings = np.load(embedding_path)
        
        # Load graph data (edge labels)
        graph_dir = os.path.join(self.GRAPH_DIR, str(graph_id))
        
        # Load node index
        node_index_path = os.path.join(graph_dir, "node_index.json")
        with open(node_index_path, "r") as f:
            node_index = json.load(f)
        
        # Load train/val/test edges with labels (format: [src, dst, label])
        train_data = np.load(os.path.join(graph_dir, "train_edges.npy"))
        val_data = np.load(os.path.join(graph_dir, "val_edges.npy"))
        test_data = np.load(os.path.join(graph_dir, "test_edges.npy"))
        
        # Extract edges and labels
        train_edges = train_data[:, :2].astype(int)
        train_labels = train_data[:, 2].astype(int)
        val_edges = val_data[:, :2].astype(int)
        val_labels = val_data[:, 2].astype(int)
        test_edges = test_data[:, :2].astype(int)
        test_labels = test_data[:, 2].astype(int)
        
        # Combine all for unified splitting in classifier
        all_edges = np.vstack([train_edges, val_edges, test_edges])
        all_labels = np.concatenate([train_labels, val_labels, test_labels])
        
        # Create feature combiner
        combiner = FeatureCombiner(method=feature_method)
        
        # Generate features
        X = []
        for edge in all_edges:
            src_emb = embeddings[edge[0]]
            dst_emb = embeddings[edge[1]]
            feature = combiner.combine(src_emb, dst_emb)
            X.append(feature)
        X = np.array(X)
        y = all_labels
        
        # Create classifier
        params = classifier_params or {}
        if classifier_type == "random_forest":
            classifier = RandomForestClassifier(random_seed=random_seed, **params)
        elif classifier_type == "xgboost":
            classifier = XGBoostClassifier(random_seed=random_seed, **params)
        elif classifier_type == "svm":
            classifier = SVMClassifier(random_seed=random_seed, **params)
        else:
            raise ValueError(f"Unknown classifier: {classifier_type}")
        
        # Train and evaluate
        metrics = classifier.train_and_evaluate(X, y, test_size=test_size, k_fold=k_fold)
        
        # Create model directory
        model_dir = os.path.join(self.MODEL_DIR, str(experiment_id))
        os.makedirs(model_dir, exist_ok=True)
        
        # Save model
        model_path = os.path.join(model_dir, f"{classifier_type}_model.pkl")
        with open(model_path, "wb") as f:
            pickle.dump(classifier.model, f)
        
        # Save metadata
        metadata_path = os.path.join(model_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump({
                "classifier": classifier_type,
                "feature_method": feature_method,
                "embedding_id": embedding_id,
                "graph_id": graph_id,
                "params": classifier_params,
                "random_seed": random_seed,
                "test_size": test_size,
                "k_fold": k_fold,
            }, f, indent=2)
        
        return metrics, model_path
    
    async def _get_embedding_or_404(self, embedding_id: int) -> Embedding:
        """Get embedding by ID or raise 404."""
        result = await self.db.execute(
            select(Embedding).where(Embedding.id == embedding_id)
        )
        embedding = result.scalar_one_or_none()
        if not embedding:
            raise HTTPException(status_code=404, detail="Embedding not found")
        return embedding
    
    async def _get_graph_or_404(self, graph_id: int) -> Graph:
        """Get graph by ID or raise 404."""
        result = await self.db.execute(
            select(Graph).where(Graph.id == graph_id)
        )
        graph = result.scalar_one_or_none()
        if not graph:
            raise HTTPException(status_code=404, detail="Graph not found")
        return graph
    
    async def get_experiment(self, experiment_id: int) -> Optional[Experiment]:
        """Get experiment by ID."""
        result = await self.db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        return result.scalar_one_or_none()
    
    async def get_experiment_or_404(self, experiment_id: int) -> Experiment:
        """Get experiment by ID or raise 404."""
        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        return experiment
    
    async def list_experiments(
        self,
        page: int = 1,
        page_size: int = 10,
        keyword: Optional[str] = None,
        embedding_id: Optional[int] = None,
        classifier: Optional[str] = None,
        status: Optional[str] = None,
    ) -> ExperimentListResponse:
        """List experiments with filtering and pagination."""
        # Build query
        query = select(Experiment)
        conditions = []
        
        if keyword:
            conditions.append(
                or_(
                    Experiment.name.ilike(f"%{keyword}%"),
                    Experiment.description.ilike(f"%{keyword}%"),
                )
            )
        
        if embedding_id is not None:
            conditions.append(Experiment.embedding_id == embedding_id)
        
        if classifier:
            conditions.append(Experiment.classifier == classifier)
        
        if status:
            conditions.append(Experiment.status == status)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(Experiment)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Experiment.created_at.desc()).offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        experiments = result.scalars().all()
        
        pages = math.ceil(total / page_size) if page_size > 0 else 0
        
        return ExperimentListResponse(
            items=[ExperimentResponse.model_validate(e) for e in experiments],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
    
    async def get_experiment_detail(self, experiment_id: int) -> ExperimentDetail:
        """Get detailed experiment information."""
        experiment = await self.get_experiment_or_404(experiment_id)
        embedding = await self._get_embedding_or_404(experiment.embedding_id)
        graph = await self._get_graph_or_404(embedding.graph_id)
        
        # Parse metrics
        metrics = None
        if experiment.status == "completed":
            metrics = MetricsResponse(
                accuracy=experiment.accuracy,
                precision=experiment.precision,
                recall=experiment.recall,
                f1_score=experiment.f1_score,
                auc_roc=experiment.auc_roc,
                auc_pr=experiment.auc_pr,
            )
        
        # Parse kfold metrics
        kfold_metrics = None
        if experiment.kfold_metrics:
            kfold_data = experiment.kfold_metrics
            kfold_metrics = KFoldMetrics(
                fold_metrics=[MetricsResponse(**m) for m in kfold_data.get("fold_metrics", [])],
                mean_metrics=MetricsResponse(**kfold_data.get("mean_metrics", {})),
                std_metrics=MetricsResponse(**kfold_data.get("std_metrics", {})),
            )
        
        # Parse feature importance
        feature_importance = None
        if experiment.feature_importance:
            importances = experiment.feature_importance.get("importances", [])
            if importances:
                # Create feature names based on feature method and embedding dim
                feature_dim = experiment.num_features or len(importances)
                emb_dim = embedding.embedding_dim
                
                if experiment.feature_method == "concat":
                    feature_names = [f"drug_{i}" for i in range(emb_dim)] + [f"disease_{i}" for i in range(emb_dim)]
                else:
                    feature_names = [f"feature_{i}" for i in range(emb_dim)]
                
                # Get top 20 features
                sorted_indices = np.argsort(importances)[::-1][:20]
                feature_importance = []
                for idx in sorted_indices:
                    if idx < len(feature_names) and idx < len(importances):
                        feature_importance.append(
                            FeatureImportanceItem(
                                feature_name=feature_names[idx],
                                importance=float(importances[idx])
                            )
                        )
        
        # Parse confusion matrix
        confusion_matrix = None
        if experiment.confusion_matrix:
            cm = experiment.confusion_matrix
            confusion_matrix = ConfusionMatrixResponse(
                tn=cm.get("tn", 0),
                fp=cm.get("fp", 0),
                fn=cm.get("fn", 0),
                tp=cm.get("tp", 0),
            )
        
        return ExperimentDetail(
            id=experiment.id,
            name=experiment.name,
            description=experiment.description,
            embedding_id=experiment.embedding_id,
            embedding_name=embedding.name,
            graph_id=graph.id,
            graph_name=graph.name,
            classifier=experiment.classifier,
            feature_method=experiment.feature_method,
            random_seed=experiment.random_seed,
            test_size=experiment.test_size,
            k_fold=experiment.k_fold,
            classifier_params=experiment.classifier_params,
            status=experiment.status,
            progress=experiment.progress,
            metrics=metrics,
            kfold_metrics=kfold_metrics,
            feature_importance=feature_importance,
            confusion_matrix=confusion_matrix,
            training_time_seconds=experiment.training_time_seconds,
            num_train_samples=experiment.num_train_samples,
            num_test_samples=experiment.num_test_samples,
            num_features=experiment.num_features,
            is_active=experiment.is_active,
            created_at=experiment.created_at,
            updated_at=experiment.updated_at,
        )
    
    async def update_experiment(
        self,
        experiment_id: int,
        update_data: ExperimentUpdate,
    ) -> Experiment:
        """Update experiment metadata."""
        experiment = await self.get_experiment_or_404(experiment_id)
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(experiment, key, value)
        
        await self.db.commit()
        await self.db.refresh(experiment)
        
        return experiment
    
    async def delete_experiment(self, experiment_id: int) -> bool:
        """Delete experiment and associated files."""
        experiment = await self.get_experiment_or_404(experiment_id)
        
        # Don't allow deletion while training
        if experiment.status == "running":
            raise HTTPException(
                status_code=400,
                detail="Cannot delete experiment while training is in progress"
            )
        
        # Delete model directory
        model_dir = os.path.join(self.MODEL_DIR, str(experiment.id))
        if os.path.exists(model_dir):
            import shutil
            try:
                shutil.rmtree(model_dir)
            except OSError:
                pass
        
        # Delete from database
        await self.db.delete(experiment)
        await self.db.commit()
        
        return True
    
    async def set_active_model(self, experiment_id: int) -> Experiment:
        """Set an experiment as the active model for predictions."""
        experiment = await self.get_experiment_or_404(experiment_id)
        
        if experiment.status != "completed":
            raise HTTPException(
                status_code=400,
                detail="Only completed experiments can be set as active"
            )
        
        # Deactivate all other experiments
        await self.db.execute(
            update(Experiment).where(Experiment.is_active == True).values(is_active=False)
        )
        
        # Activate this experiment
        experiment.is_active = True
        await self.db.commit()
        await self.db.refresh(experiment)
        
        return experiment
    
    async def get_active_model(self) -> Optional[Experiment]:
        """Get the currently active model."""
        result = await self.db.execute(
            select(Experiment).where(Experiment.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def compare_experiments(self, experiment_ids: List[int]) -> Dict[str, Any]:
        """Compare multiple experiments."""
        experiments = []
        for exp_id in experiment_ids:
            exp = await self.get_experiment(exp_id)
            if exp and exp.status == "completed":
                experiments.append(ExperimentResponse.model_validate(exp))
        
        if not experiments:
            return {"experiments": [], "best_by_auc_roc": None, "best_by_f1": None}
        
        # Find best models
        best_auc_roc = max(experiments, key=lambda x: x.auc_roc or 0)
        best_f1 = max(experiments, key=lambda x: x.f1_score or 0)
        
        return {
            "experiments": experiments,
            "best_by_auc_roc": best_auc_roc.id if best_auc_roc.auc_roc else None,
            "best_by_f1": best_f1.id if best_f1.f1_score else None,
        }
    
    async def get_experiments_by_embedding(self, embedding_id: int) -> List[Experiment]:
        """Get all experiments for an embedding."""
        result = await self.db.execute(
            select(Experiment)
            .where(Experiment.embedding_id == embedding_id)
            .order_by(Experiment.created_at.desc())
        )
        return list(result.scalars().all())
