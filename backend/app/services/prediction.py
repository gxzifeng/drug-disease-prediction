import os
import json
import math
import pickle
import numpy as np
import pandas as pd
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.config import settings
from app.models.experiment import Experiment
from app.models.embedding import Embedding
from app.models.graph import Graph
from app.models.dataset import Dataset, DatasetRecord
from app.models.prediction import Prediction
from app.schemas.prediction import PredictionResponse, PredictionRequest
from app.algorithms.classifiers import FeatureCombiner
from app.services.experiment import ExperimentService
from app.services.graph import GraphService

class PredictionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.experiment_service = ExperimentService(db)
        self.graph_service = GraphService(db)

    async def _get_model_and_resources(self, model_id: Optional[int]) -> Tuple[Experiment, Embedding, Any, Dict, np.ndarray]:
        # Get model
        if model_id:
            experiment = await self.experiment_service.get_experiment_or_404(model_id)
        else:
            experiment = await self.experiment_service.get_active_model()
            if not experiment:
                raise HTTPException(status_code=400, detail="No active model found. Please specify a model_id or set an active model.")

        if experiment.status != "completed":
            raise HTTPException(status_code=400, detail="Model training is not completed.")

        # Get embedding
        embedding_result = await self.db.execute(select(Embedding).where(Embedding.id == experiment.embedding_id))
        embedding = embedding_result.scalar_one_or_none()
        if not embedding:
            raise HTTPException(status_code=404, detail="Embedding not found")

        # Load node index
        node_index = await self.graph_service.get_node_index(embedding.graph_id)
        
        # Load embeddings
        if not os.path.exists(embedding.embedding_path):
            raise HTTPException(status_code=404, detail="Embedding file not found")
        embeddings_data = np.load(embedding.embedding_path)

        # Load model
        if not experiment.model_path or not os.path.exists(experiment.model_path):
            raise HTTPException(status_code=404, detail="Model file not found")
        
        with open(experiment.model_path, "rb") as f:
            model = pickle.load(f)

        return experiment, embedding, model, node_index, embeddings_data

    async def predict_single(self, request: PredictionRequest) -> PredictionResponse:
        experiment, embedding, model, node_index, embeddings_data = await self._get_model_and_resources(request.model_id)

        # Check if drug and disease exist in node index
        if request.drug_id not in node_index.drug_to_idx:
            raise HTTPException(status_code=400, detail=f"Drug ID {request.drug_id} not found in model's graph")
        if request.disease_id not in node_index.disease_to_idx:
            raise HTTPException(status_code=400, detail=f"Disease ID {request.disease_id} not found in model's graph")

        drug_idx = node_index.drug_to_idx[request.drug_id]
        disease_idx = node_index.disease_to_idx[request.disease_id]

        drug_emb = embeddings_data[drug_idx]
        disease_emb = embeddings_data[disease_idx]

        # Combine features
        combiner = FeatureCombiner(method=experiment.feature_method)
        feature = combiner.combine(drug_emb, disease_emb)
        X = feature.reshape(1, -1)

        # Predict
        probability = float(model.predict_proba(X)[0][1])
        label = int(model.predict(X)[0])

        return PredictionResponse(
            drug_id=request.drug_id,
            disease_id=request.disease_id,
            probability=probability,
            label=label,
            model_id=experiment.id,
            model_name=experiment.name
        )

    async def _log_prediction(
        self,
        *,
        type: str,
        experiment_id: Optional[int],
        user_id: Optional[int],
        input_data: Dict[str, Any],
        result: Optional[Dict[str, Any]],
        status: str = "completed",
        task_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Prediction:
        """Persist a prediction record for history queries."""
        prediction = Prediction(
            type=type,
            experiment_id=experiment_id,
            user_id=user_id,
            input_data=input_data,
            result=result,
            status=status,
            task_id=task_id,
            error_message=error_message,
        )

        self.db.add(prediction)
        await self.db.commit()
        await self.db.refresh(prediction)
        return prediction

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        from app.core.celery_app import celery_app
        task = celery_app.AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": task.status,
            "progress": 0,
            "result": None,
            "message": None
        }

        if task.status == "PROGRESS":
            info = task.info or {}
            response["progress"] = info.get("progress", 0)
            response["message"] = info.get("message", "")
        elif task.status == "SUCCESS":
            response["progress"] = 100
            response["result"] = task.result
        elif task.status == "FAILURE":
            response["status"] = "FAILURE"
            response["message"] = str(task.info)
        
        return response

    async def recommend_drugs(
        self,
        disease_id: str,
        top_k: int = 10,
        model_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Recommend top-K drugs for a given disease using the trained classifier.
        """
        experiment, embedding, model, node_index, embeddings_data = await self._get_model_and_resources(model_id)

        if disease_id not in node_index.disease_to_idx:
            raise HTTPException(
                status_code=400,
                detail=f"Disease ID {disease_id} not found in model's graph",
            )

        disease_idx = node_index.disease_to_idx[disease_id]
        disease_emb = embeddings_data[disease_idx]

        combiner = FeatureCombiner(method=experiment.feature_method)

        results: List[Dict[str, Any]] = []
        for drug_id, drug_idx in node_index.drug_to_idx.items():
            drug_emb = embeddings_data[drug_idx]
            feature = combiner.combine(drug_emb, disease_emb)
            X = feature.reshape(1, -1)

            probability = float(model.predict_proba(X)[0][1])
            try:
                label = int(model.predict(X)[0])
            except Exception:
                label = None

            results.append(
                {
                    "drug_id": drug_id,
                    "probability": probability,
                    "label": label,
                }
            )

        # Sort and take top K
        results.sort(key=lambda x: x["probability"], reverse=True)
        top_items = results[:top_k]

        # Log prediction history
        await self._log_prediction(
            type="recommendation",
            experiment_id=experiment.id,
            user_id=user_id,
            input_data={
                "mode": "disease_to_drugs",
                "disease_id": disease_id,
                "top_k": top_k,
            },
            result={
                "items": top_items,
            },
            status="completed",
        )

        return {
            "disease_id": disease_id,
            "disease_name": None,
            "model_id": experiment.id,
            "model_name": experiment.name,
            "items": top_items,
        }

    async def recommend_diseases(
        self,
        drug_id: str,
        top_k: int = 10,
        model_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Recommend top-K diseases for a given drug using the trained classifier.
        """
        experiment, embedding, model, node_index, embeddings_data = await self._get_model_and_resources(model_id)

        if drug_id not in node_index.drug_to_idx:
            raise HTTPException(
                status_code=400,
                detail=f"Drug ID {drug_id} not found in model's graph",
            )

        drug_idx = node_index.drug_to_idx[drug_id]
        drug_emb = embeddings_data[drug_idx]

        combiner = FeatureCombiner(method=experiment.feature_method)

        results: List[Dict[str, Any]] = []
        for disease_id, disease_idx in node_index.disease_to_idx.items():
            disease_emb = embeddings_data[disease_idx]
            feature = combiner.combine(drug_emb, disease_emb)
            X = feature.reshape(1, -1)

            probability = float(model.predict_proba(X)[0][1])
            try:
                label = int(model.predict(X)[0])
            except Exception:
                label = None

            results.append(
                {
                    "disease_id": disease_id,
                    "probability": probability,
                    "label": label,
                }
            )

        # Sort and take top K
        results.sort(key=lambda x: x["probability"], reverse=True)
        top_items = results[:top_k]

        # Log prediction history
        await self._log_prediction(
            type="recommendation",
            experiment_id=experiment.id,
            user_id=user_id,
            input_data={
                "mode": "drug_to_diseases",
                "drug_id": drug_id,
                "top_k": top_k,
            },
            result={
                "items": top_items,
            },
            status="completed",
        )

        return {
            "drug_id": drug_id,
            "drug_name": None,
            "model_id": experiment.id,
            "model_name": experiment.name,
            "items": top_items,
        }

    async def predict_batch(self, update_state_func, dataset_id: Optional[int], model_id: Optional[int], task_id: str) -> Dict[str, Any]:
        # Update progress
        update_state_func(state="PROGRESS", meta={"progress": 5, "message": "Loading model and resources..."})
        
        experiment, embedding, model, node_index, embeddings_data = await self._get_model_and_resources(model_id)
        
        # Get pairs to predict
        update_state_func(state="PROGRESS", meta={"progress": 10, "message": "Fetching pairs to predict..."})
        
        pairs = []
        if dataset_id:
            result = await self.db.execute(select(DatasetRecord).where(DatasetRecord.dataset_id == dataset_id))
            records = result.scalars().all()
            for r in records:
                pairs.append((r.drug_id, r.disease_id))
        else:
            raise ValueError("dataset_id is required for batch prediction")

        if not pairs:
            return {"status": "error", "message": "No pairs found to predict"}

        update_state_func(state="PROGRESS", meta={"progress": 20, "message": f"Starting prediction for {len(pairs)} pairs..."})
        
        results = []
        combiner = FeatureCombiner(method=experiment.feature_method)
        
        total = len(pairs)
        for i, (drug_id, disease_id) in enumerate(pairs):
            if i % 100 == 0:
                progress = 20 + int((i / total) * 70)
                update_state_func(state="PROGRESS", meta={"progress": progress, "message": f"Predicting... {i}/{total}"})
            
            if drug_id in node_index.drug_to_idx and disease_id in node_index.disease_to_idx:
                drug_idx = node_index.drug_to_idx[drug_id]
                disease_idx = node_index.disease_to_idx[disease_id]
                
                drug_emb = embeddings_data[drug_idx]
                disease_emb = embeddings_data[disease_idx]
                
                feature = combiner.combine(drug_emb, disease_emb)
                X = feature.reshape(1, -1)
                
                probability = float(model.predict_proba(X)[0][1])
                label = int(model.predict(X)[0])
                
                results.append({
                    "drug_id": drug_id,
                    "disease_id": disease_id,
                    "probability": probability,
                    "label": label
                })

        update_state_func(state="PROGRESS", meta={"progress": 95, "message": "Saving results..."})
        
        # Save to CSV
        os.makedirs(settings.PREDICTION_DIR, exist_ok=True)
        filename = f"prediction_{task_id}.csv"
        filepath = os.path.join(settings.PREDICTION_DIR, filename)
        
        df = pd.DataFrame(results)
        df.to_csv(filepath, index=False)
        
        return {
            "status": "completed",
            "total_pairs": total,
            "predicted_pairs": len(results),
            "filename": filename,
            "download_url": f"/api/v1/predictions/download/{filename}",
            "completed_at": datetime.utcnow().isoformat()
        }

    async def get_history(
        self,
        page: int = 1,
        page_size: int = 10,
        type: Optional[str] = None,
        experiment_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get paginated prediction history.

        By default, if user_id is provided, only that user's history is returned.
        """
        if page_size <= 0:
            page_size = 10

        # Build base query
        query = select(Prediction)
        count_query = select(func.count()).select_from(Prediction)

        if type:
            query = query.where(Prediction.type == type)
            count_query = count_query.where(Prediction.type == type)

        if experiment_id is not None:
            query = query.where(Prediction.experiment_id == experiment_id)
            count_query = count_query.where(Prediction.experiment_id == experiment_id)

        if user_id is not None:
            query = query.where(Prediction.user_id == user_id)
            count_query = count_query.where(Prediction.user_id == user_id)

        # Total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Pagination
        offset = (page - 1) * page_size
        query = query.order_by(Prediction.created_at.desc()).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        rows: List[Prediction] = result.scalars().all()

        pages = math.ceil(total / page_size) if page_size > 0 else 0

        items: List[Dict[str, Any]] = []
        for p in rows:
            items.append(
                {
                    "id": p.id,
                    "type": p.type,
                    "experiment_id": p.experiment_id,
                    "user_id": p.user_id,
                    "task_id": p.task_id,
                    "status": p.status,
                    "error_message": p.error_message,
                    "input_data": p.input_data,
                    "result": p.result,
                    "created_at": p.created_at,
                    "completed_at": p.completed_at,
                }
            )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
        }

    async def get_top_predictions(
        self,
        model_id: int,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Get top predicted associations as a subgraph.
        
        Currently, this evaluates the test set and returns the top predicted associations.
        In a full implementation, this could explore unseen pairs.
        """
        experiment, embedding, model, node_index, embeddings_data = await self._get_model_and_resources(model_id)
        
        graph_dir = os.path.join(settings.GRAPH_DIR, str(embedding.graph_id))
        test_edges_path = os.path.join(graph_dir, "test_edges.npy")
        
        if not os.path.exists(test_edges_path):
            raise HTTPException(status_code=400, detail="Graph split data not found")
            
        test_data = np.load(test_edges_path)
        
        # Extract edges
        edges = test_data[:, :2].astype(int)
        
        combiner = FeatureCombiner(method=experiment.feature_method)
        
        # Predict for all test edges
        results = []
        for edge in edges:
            src_idx, dst_idx = edge[0], edge[1]
            src_emb = embeddings_data[src_idx]
            dst_emb = embeddings_data[dst_idx]
            
            feature = combiner.combine(src_emb, dst_emb)
            X = feature.reshape(1, -1)
            
            probability = float(model.predict_proba(X)[0][1])
            results.append((src_idx, dst_idx, probability))
            
        # Sort by probability and take top K
        results.sort(key=lambda x: x[2], reverse=True)
        top_results = results[:limit]
        
        # Build subgraph
        idx_to_drug = node_index.idx_to_drug
        idx_to_disease = node_index.idx_to_disease
        
        nodes_dict = {}
        edges_list = []
        
        for src_idx, dst_idx, prob in top_results:
            src_id = idx_to_drug.get(src_idx) or idx_to_disease.get(src_idx)
            dst_id = idx_to_drug.get(dst_idx) or idx_to_disease.get(dst_idx)
            
            if src_id not in nodes_dict:
                nodes_dict[src_id] = {
                    "id": src_id,
                    "name": src_id,
                    "type": "drug" if src_idx in idx_to_drug else "disease"
                }
            
            if dst_id not in nodes_dict:
                nodes_dict[dst_id] = {
                    "id": dst_id,
                    "name": dst_id,
                    "type": "drug" if dst_idx in idx_to_drug else "disease"
                }
                
            edges_list.append({
                "source": src_id,
                "target": dst_id,
                "label": 1,
                "type": "predicted",
                "weight": prob
            })
            
        return {
            "nodes": list(nodes_dict.values()),
            "edges": edges_list
        }
