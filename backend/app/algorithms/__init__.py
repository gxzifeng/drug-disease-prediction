"""Algorithms package for drug-disease prediction."""
from .embeddings import Node2VecTrainer, BaseEmbeddingTrainer
from .gnn import GCNTrainer

__all__ = ["Node2VecTrainer", "GCNTrainer", "BaseEmbeddingTrainer"]
