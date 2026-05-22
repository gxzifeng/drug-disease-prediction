"""Embedding algorithms package."""
from .node2vec import Node2VecTrainer
from .base import BaseEmbeddingTrainer

__all__ = ["Node2VecTrainer", "BaseEmbeddingTrainer"]
