"""Graph service for building drug-disease bipartite graphs."""
import os
import json
import math
import numpy as np
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.graph import Graph
from app.models.dataset import Dataset, DatasetRecord
from app.schemas.graph import (
    GraphBuildRequest,
    GraphResponse,
    GraphListResponse,
    GraphSummary,
    NodeIndexMapping,
    GraphUpdate,
)


class GraphService:
    """Service class for graph operations."""
    
    GRAPH_DIR = "data/graphs"
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def build_graph(
        self,
        request: GraphBuildRequest,
        user_id: Optional[int] = None,
    ) -> Graph:
        """Build a bipartite graph from dataset."""
        # Validate ratios
        total_ratio = request.train_ratio + request.val_ratio + request.test_ratio
        if abs(total_ratio - 1.0) > 0.001:
            raise HTTPException(
                status_code=400,
                detail=f"Train/val/test ratios must sum to 1.0, got {total_ratio:.3f}"
            )
        
        # Check dataset exists and is parsed
        dataset = await self._get_dataset_or_404(request.dataset_id)
        if not dataset.is_parsed:
            raise HTTPException(
                status_code=400,
                detail="Dataset has not been successfully parsed"
            )
        
        # Create graph record
        graph = Graph(
            name=request.name,
            description=request.description,
            dataset_id=request.dataset_id,
            negative_sample_ratio=request.negative_sample_ratio,
            train_ratio=request.train_ratio,
            val_ratio=request.val_ratio,
            test_ratio=request.test_ratio,
            random_seed=request.random_seed,
            created_by=user_id,
        )
        
        self.db.add(graph)
        await self.db.flush()
        
        try:
            # Build the graph
            await self._build_bipartite_graph(graph, dataset)
            graph.is_built = True
        except Exception as e:
            graph.build_error = str(e)
            graph.is_built = False
        
        await self.db.commit()
        await self.db.refresh(graph)
        
        return graph
    
    async def _build_bipartite_graph(self, graph: Graph, dataset: Dataset) -> None:
        """Build bipartite graph structure from dataset records."""
        # Set random seed for reproducibility
        np.random.seed(graph.random_seed)
        
        # Fetch all records from dataset
        result = await self.db.execute(
            select(DatasetRecord).where(DatasetRecord.dataset_id == dataset.id)
        )
        records = result.scalars().all()
        
        if not records:
            raise ValueError("Dataset has no records")
        
        # Build node mappings
        drugs = sorted(set(r.drug_id for r in records))
        diseases = sorted(set(r.disease_id for r in records))
        
        drug_to_idx = {drug: idx for idx, drug in enumerate(drugs)}
        disease_to_idx = {disease: idx + len(drugs) for idx, disease in enumerate(diseases)}
        
        # Build edges from positive samples
        positive_edges = []
        positive_set = set()  # For quick lookup during negative sampling
        
        for record in records:
            if record.label == 1:
                drug_idx = drug_to_idx[record.drug_id]
                disease_idx = disease_to_idx[record.disease_id]
                positive_edges.append((drug_idx, disease_idx))
                positive_set.add((record.drug_id, record.disease_id))
        
        num_positive = len(positive_edges)
        
        # Generate negative samples
        num_negative = int(num_positive * graph.negative_sample_ratio)
        negative_edges = []
        
        # Check if dataset already has negative samples
        existing_negatives = [(r.drug_id, r.disease_id) for r in records if r.label == 0]
        
        if existing_negatives:
            # Use existing negative samples
            for drug_id, disease_id in existing_negatives[:num_negative]:
                drug_idx = drug_to_idx[drug_id]
                disease_idx = disease_to_idx[disease_id]
                negative_edges.append((drug_idx, disease_idx))
        
        # Generate more negative samples if needed
        remaining_negatives = num_negative - len(negative_edges)
        if remaining_negatives > 0:
            generated_negatives = self._generate_negative_samples(
                drugs, diseases, positive_set, remaining_negatives
            )
            for drug_id, disease_id in generated_negatives:
                drug_idx = drug_to_idx[drug_id]
                disease_idx = disease_to_idx[disease_id]
                negative_edges.append((drug_idx, disease_idx))
        
        # Combine all edges with labels
        all_edges = [(e[0], e[1], 1) for e in positive_edges] + [(e[0], e[1], 0) for e in negative_edges]
        np.random.shuffle(all_edges)
        
        # Split into train/val/test
        n_total = len(all_edges)
        n_train = int(n_total * graph.train_ratio)
        n_val = int(n_total * graph.val_ratio)
        
        train_edges = all_edges[:n_train]
        val_edges = all_edges[n_train:n_train + n_val]
        test_edges = all_edges[n_train + n_val:]
        
        # Create graph directory
        graph_dir = os.path.join(self.GRAPH_DIR, str(graph.id))
        os.makedirs(graph_dir, exist_ok=True)
        
        # Save node index mapping
        node_index = {
            "drug_to_idx": drug_to_idx,
            "disease_to_idx": disease_to_idx,
            "idx_to_drug": {str(v): k for k, v in drug_to_idx.items()},
            "idx_to_disease": {str(v): k for k, v in disease_to_idx.items()},
        }
        node_index_path = os.path.join(graph_dir, "node_index.json")
        with open(node_index_path, "w", encoding="utf-8") as f:
            json.dump(node_index, f, ensure_ascii=False, indent=2)
        
        # Save edge index (all edges as numpy array)
        edge_data = np.array(all_edges)
        edge_index_path = os.path.join(graph_dir, "edge_index.npy")
        np.save(edge_index_path, edge_data)
        
        # Save train/val/test splits
        train_mask_path = os.path.join(graph_dir, "train_edges.npy")
        val_mask_path = os.path.join(graph_dir, "val_edges.npy")
        test_mask_path = os.path.join(graph_dir, "test_edges.npy")
        
        np.save(train_mask_path, np.array(train_edges))
        np.save(val_mask_path, np.array(val_edges))
        np.save(test_mask_path, np.array(test_edges))
        
        # Update graph statistics
        graph.num_drug_nodes = len(drugs)
        graph.num_disease_nodes = len(diseases)
        graph.num_total_nodes = len(drugs) + len(diseases)
        graph.num_edges = len(all_edges)
        graph.num_positive_edges = num_positive
        graph.num_negative_edges = len(negative_edges)
        graph.num_train_edges = len(train_edges)
        graph.num_val_edges = len(val_edges)
        graph.num_test_edges = len(test_edges)
        
        # Store file paths
        graph.node_index_path = node_index_path
        graph.edge_index_path = edge_index_path
        graph.train_mask_path = train_mask_path
        graph.val_mask_path = val_mask_path
        graph.test_mask_path = test_mask_path
        
        # Store additional metadata
        graph.metadata = {
            "drugs": drugs,
            "diseases": diseases,
            "build_timestamp": datetime.utcnow().isoformat(),
        }
    
    def _generate_negative_samples(
        self,
        drugs: List[str],
        diseases: List[str],
        positive_set: set,
        num_samples: int,
    ) -> List[Tuple[str, str]]:
        """Generate random negative samples not in positive set."""
        negative_samples = []
        max_attempts = num_samples * 10  # Prevent infinite loop
        attempts = 0
        
        while len(negative_samples) < num_samples and attempts < max_attempts:
            drug = np.random.choice(drugs)
            disease = np.random.choice(diseases)
            
            if (drug, disease) not in positive_set:
                negative_samples.append((drug, disease))
                positive_set.add((drug, disease))  # Avoid duplicates
            
            attempts += 1
        
        return negative_samples
    
    async def _get_dataset_or_404(self, dataset_id: int) -> Dataset:
        """Get dataset by ID or raise 404."""
        result = await self.db.execute(
            select(Dataset).where(Dataset.id == dataset_id)
        )
        dataset = result.scalar_one_or_none()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        return dataset
    
    async def get_graph(self, graph_id: int) -> Optional[Graph]:
        """Get graph by ID."""
        result = await self.db.execute(
            select(Graph).where(Graph.id == graph_id)
        )
        return result.scalar_one_or_none()
    
    async def get_graph_or_404(self, graph_id: int) -> Graph:
        """Get graph by ID or raise 404."""
        graph = await self.get_graph(graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="Graph not found")
        return graph
    
    async def list_graphs(
        self,
        page: int = 1,
        page_size: int = 10,
        keyword: Optional[str] = None,
        dataset_id: Optional[int] = None,
        is_built: Optional[bool] = None,
    ) -> GraphListResponse:
        """List graphs with filtering and pagination."""
        # Build query
        query = select(Graph)
        conditions = []
        
        if keyword:
            conditions.append(
                or_(
                    Graph.name.ilike(f"%{keyword}%"),
                    Graph.description.ilike(f"%{keyword}%"),
                )
            )
        
        if dataset_id is not None:
            conditions.append(Graph.dataset_id == dataset_id)
        
        if is_built is not None:
            # 兼容旧表结构：通过产物路径判断是否已构建
            built_condition = and_(
                Graph.node_index_path.is_not(None),
                Graph.edge_index_path.is_not(None),
                Graph.train_mask_path.is_not(None),
                Graph.val_mask_path.is_not(None),
                Graph.test_mask_path.is_not(None),
            )
            if is_built:
                conditions.append(built_condition)
            else:
                conditions.append(~built_condition)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(Graph)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Graph.created_at.desc()).offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        graphs = result.scalars().all()
        
        pages = math.ceil(total / page_size) if page_size > 0 else 0
        
        return GraphListResponse(
            items=[GraphResponse.model_validate(g) for g in graphs],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
    
    async def get_graph_summary(self, graph_id: int) -> GraphSummary:
        """Get detailed summary of a graph."""
        graph = await self.get_graph_or_404(graph_id)
        
        # Get dataset info
        dataset = await self._get_dataset_or_404(graph.dataset_id)
        
        # Calculate ratios
        total_edges = graph.num_edges if graph.num_edges > 0 else 1
        positive_ratio = graph.num_positive_edges / total_edges
        train_ratio_actual = graph.num_train_edges / total_edges
        val_ratio_actual = graph.num_val_edges / total_edges
        test_ratio_actual = graph.num_test_edges / total_edges
        
        return GraphSummary(
            id=graph.id,
            name=graph.name,
            dataset_id=graph.dataset_id,
            dataset_name=dataset.name,
            num_drug_nodes=graph.num_drug_nodes,
            num_disease_nodes=graph.num_disease_nodes,
            num_total_nodes=graph.num_total_nodes,
            num_edges=graph.num_edges,
            num_positive_edges=graph.num_positive_edges,
            num_negative_edges=graph.num_negative_edges,
            positive_ratio=round(positive_ratio, 4),
            num_train_edges=graph.num_train_edges,
            num_val_edges=graph.num_val_edges,
            num_test_edges=graph.num_test_edges,
            train_ratio_actual=round(train_ratio_actual, 4),
            val_ratio_actual=round(val_ratio_actual, 4),
            test_ratio_actual=round(test_ratio_actual, 4),
            negative_sample_ratio=graph.negative_sample_ratio,
            random_seed=graph.random_seed,
            is_built=graph.is_built,
            created_at=graph.created_at,
        )
    
    async def get_node_index(self, graph_id: int) -> NodeIndexMapping:
        """Get node index mapping for a graph."""
        graph = await self.get_graph_or_404(graph_id)
        
        if not graph.is_built or not graph.node_index_path:
            raise HTTPException(
                status_code=400,
                detail="Graph has not been built successfully"
            )
        
        if not os.path.exists(graph.node_index_path):
            raise HTTPException(
                status_code=404,
                detail="Node index file not found"
            )
        
        with open(graph.node_index_path, "r", encoding="utf-8") as f:
            node_index = json.load(f)
        
        return NodeIndexMapping(
            drug_to_idx=node_index["drug_to_idx"],
            disease_to_idx=node_index["disease_to_idx"],
            idx_to_drug={int(k): v for k, v in node_index["idx_to_drug"].items()},
            idx_to_disease={int(k): v for k, v in node_index["idx_to_disease"].items()},
        )
    
    async def update_graph(
        self,
        graph_id: int,
        update_data: GraphUpdate,
    ) -> Graph:
        """Update graph metadata."""
        graph = await self.get_graph_or_404(graph_id)
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(graph, key, value)
        
        await self.db.commit()
        await self.db.refresh(graph)
        
        return graph
    
    async def delete_graph(self, graph_id: int) -> bool:
        """Delete graph and associated files."""
        graph = await self.get_graph_or_404(graph_id)
        
        # Delete graph directory
        graph_dir = os.path.join(self.GRAPH_DIR, str(graph.id))
        if os.path.exists(graph_dir):
            import shutil
            try:
                shutil.rmtree(graph_dir)
            except OSError:
                pass  # Directory may already be deleted
        
        # Delete from database
        await self.db.delete(graph)
        await self.db.commit()
        
        return True
    
    async def get_graphs_by_dataset(self, dataset_id: int) -> List[Graph]:
        """Get all graphs built from a specific dataset."""
        result = await self.db.execute(
            select(Graph).where(Graph.dataset_id == dataset_id).order_by(Graph.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_subgraph(
        self,
        graph_id: int,
        limit: int = 100,
        node_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a subgraph for visualization.
        
        If node_id is provided, returns the neighborhood of that node.
        Otherwise, returns a random sample of edges.
        """
        graph = await self.get_graph_or_404(graph_id)
        
        if not graph.is_built or not graph.edge_index_path or not graph.node_index_path:
            raise HTTPException(
                status_code=400,
                detail="Graph has not been built successfully"
            )
        
        # Load node index mapping
        with open(graph.node_index_path, "r", encoding="utf-8") as f:
            node_index = json.load(f)
        
        idx_to_drug = {int(k): v for k, v in node_index["idx_to_drug"].items()}
        idx_to_disease = {int(k): v for k, v in node_index["idx_to_disease"].items()}
        
        drug_to_idx = node_index["drug_to_idx"]
        disease_to_idx = node_index["disease_to_idx"]
        
        # Load all edges
        all_edges = np.load(graph.edge_index_path)
        
        selected_edges = []
        if node_id:
            # Find the index of the node
            target_idx = drug_to_idx.get(node_id) or disease_to_idx.get(node_id)
            if target_idx is None:
                raise HTTPException(status_code=404, detail=f"Node {node_id} not found in graph")
            
            # Find edges connected to this node
            mask = (all_edges[:, 0] == target_idx) | (all_edges[:, 1] == target_idx)
            selected_edges = all_edges[mask]
            if len(selected_edges) > limit:
                selected_edges = selected_edges[:limit]
        else:
            # Randomly sample edges
            # Prefer positive edges for visualization
            positive_mask = all_edges[:, 2] == 1
            positive_edges = all_edges[positive_mask]
            
            if len(positive_edges) > limit:
                indices = np.random.choice(len(positive_edges), limit, replace=False)
                selected_edges = positive_edges[indices]
            else:
                selected_edges = positive_edges
                
        # Build node and edge lists
        nodes_dict = {}
        edges_list = []
        
        for edge in selected_edges:
            src_idx, dst_idx, label = int(edge[0]), int(edge[1]), int(edge[2])
            
            # Get node IDs and names
            src_id = idx_to_drug.get(src_idx) or idx_to_disease.get(src_idx)
            dst_id = idx_to_drug.get(dst_idx) or idx_to_disease.get(dst_idx)
            
            if src_id not in nodes_dict:
                nodes_dict[src_id] = {
                    "id": src_id,
                    "name": src_id,  # In a real app, we'd look up the name in the DB
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
                "label": label,
                "type": "original"
            })
            
        return {
            "nodes": list(nodes_dict.values()),
            "edges": edges_list
        }
