"""Base class for embedding trainers."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List, Callable
import numpy as np


class BaseEmbeddingTrainer(ABC):
    """Abstract base class for embedding training algorithms."""
    
    def __init__(
        self,
        embedding_dim: int = 64,
        epochs: int = 100,
        learning_rate: float = 0.01,
        random_seed: int = 42,
        progress_callback: Optional[Callable[[int, float, Optional[float]], None]] = None,
    ):
        """
        Initialize trainer.
        
        Args:
            embedding_dim: Dimension of the output embeddings
            epochs: Number of training epochs
            learning_rate: Learning rate
            random_seed: Random seed for reproducibility
            progress_callback: Callback function(epoch, train_loss, val_loss) for progress updates
        """
        self.embedding_dim = embedding_dim
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.random_seed = random_seed
        self.progress_callback = progress_callback
        
        # Set random seeds
        np.random.seed(random_seed)
        
        # Training history
        self.history: Dict[str, List[float]] = {
            "train_losses": [],
            "val_losses": [],
            "epochs": [],
        }
    
    @abstractmethod
    def train(
        self,
        node_index: Dict[str, Dict[str, int]],
        edge_index: np.ndarray,
        train_edges: np.ndarray,
        val_edges: np.ndarray,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Train embeddings.
        
        Args:
            node_index: Node index mapping (drug_to_idx, disease_to_idx)
            edge_index: All edges as numpy array with shape (num_edges, 3) [src, dst, label]
            train_edges: Training edges
            val_edges: Validation edges
            
        Returns:
            Tuple of (embeddings array, training metadata)
        """
        pass
    
    @abstractmethod
    def save(self, embedding_path: str, model_path: Optional[str] = None) -> None:
        """Save trained embeddings and optionally the model."""
        pass
    
    @abstractmethod
    def load(self, embedding_path: str, model_path: Optional[str] = None) -> np.ndarray:
        """Load trained embeddings and optionally the model."""
        pass
    
    def get_history(self) -> Dict[str, List[float]]:
        """Get training history."""
        return self.history
    
    def _report_progress(self, epoch: int, train_loss: float, val_loss: Optional[float] = None):
        """Report training progress via callback."""
        self.history["epochs"].append(epoch)
        self.history["train_losses"].append(train_loss)
        if val_loss is not None:
            self.history["val_losses"].append(val_loss)
        
        if self.progress_callback:
            self.progress_callback(epoch, train_loss, val_loss)
