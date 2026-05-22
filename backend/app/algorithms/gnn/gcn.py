"""GCN (Graph Convolutional Network) embedding implementation.

This is a numpy-based implementation that doesn't require PyTorch or PyTorch Geometric.
For production use with large graphs, consider using the PyTorch Geometric version.
"""
import os
import json
import time
from typing import Dict, Any, Optional, Tuple, List, Callable
import numpy as np
from collections import defaultdict

from app.algorithms.embeddings.base import BaseEmbeddingTrainer


class GCNTrainer(BaseEmbeddingTrainer):
    """
    GCN embedding trainer using numpy.
    
    Implements a simple GCN for link prediction in bipartite graphs.
    Based on: Kipf & Welling, "Semi-Supervised Classification with Graph Convolutional Networks", ICLR 2017
    """
    
    def __init__(
        self,
        embedding_dim: int = 64,
        epochs: int = 100,
        learning_rate: float = 0.01,
        random_seed: int = 42,
        hidden_channels: int = 64,
        num_layers: int = 2,
        dropout: float = 0.5,
        progress_callback: Optional[Callable[[int, float, Optional[float]], None]] = None,
    ):
        """
        Initialize GCN trainer.
        
        Args:
            embedding_dim: Output embedding dimension
            epochs: Number of training epochs
            learning_rate: Learning rate
            random_seed: Random seed
            hidden_channels: Hidden layer dimension
            num_layers: Number of GCN layers
            dropout: Dropout rate
            progress_callback: Callback for progress updates
        """
        super().__init__(embedding_dim, epochs, learning_rate, random_seed, progress_callback)
        
        self.hidden_channels = hidden_channels
        self.num_layers = num_layers
        self.dropout = dropout
        
        # Model parameters
        self.weights: List[np.ndarray] = []
        self.embeddings: Optional[np.ndarray] = None
        self.num_nodes: int = 0
        self.adj_norm: Optional[np.ndarray] = None
    
    def _build_adjacency(self, edge_index: np.ndarray, num_nodes: int) -> np.ndarray:
        """Build normalized adjacency matrix."""
        # Build adjacency matrix (only from positive edges)
        adj = np.zeros((num_nodes, num_nodes), dtype=np.float32)
        
        for edge in edge_index:
            src, dst, label = int(edge[0]), int(edge[1]), int(edge[2])
            if label == 1:
                adj[src, dst] = 1.0
                adj[dst, src] = 1.0  # Symmetric
        
        # Add self-loops
        adj = adj + np.eye(num_nodes, dtype=np.float32)
        
        # Compute degree matrix
        degree = np.sum(adj, axis=1)
        degree_inv_sqrt = np.power(degree, -0.5, where=degree > 0)
        degree_inv_sqrt[degree == 0] = 0.0
        
        # Normalize: D^{-1/2} A D^{-1/2}
        D_inv_sqrt = np.diag(degree_inv_sqrt)
        adj_norm = D_inv_sqrt @ adj @ D_inv_sqrt
        
        return adj_norm
    
    def _init_weights(self, input_dim: int) -> None:
        """Initialize layer weights using Xavier initialization."""
        self.weights = []
        
        dims = [input_dim]
        for i in range(self.num_layers - 1):
            dims.append(self.hidden_channels)
        dims.append(self.embedding_dim)
        
        for i in range(len(dims) - 1):
            # Xavier initialization
            scale = np.sqrt(2.0 / (dims[i] + dims[i + 1]))
            W = np.random.randn(dims[i], dims[i + 1]).astype(np.float32) * scale
            self.weights.append(W)
    
    def _relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU activation."""
        return np.maximum(0, x)
    
    def _relu_derivative(self, x: np.ndarray) -> np.ndarray:
        """ReLU derivative."""
        return (x > 0).astype(np.float32)
    
    def _dropout_mask(self, shape: Tuple, training: bool = True) -> np.ndarray:
        """Generate dropout mask."""
        if not training or self.dropout == 0:
            return np.ones(shape, dtype=np.float32)
        mask = (np.random.random(shape) > self.dropout).astype(np.float32)
        return mask / (1 - self.dropout)
    
    def _forward(self, X: np.ndarray, training: bool = True) -> Tuple[np.ndarray, List]:
        """Forward pass through GCN layers."""
        H = X
        layer_outputs = [H]
        
        for i, W in enumerate(self.weights):
            # Graph convolution: H = σ(A_norm @ H @ W)
            H = self.adj_norm @ H @ W
            
            # Activation (except last layer)
            if i < len(self.weights) - 1:
                H = self._relu(H)
                
                # Dropout
                if training:
                    mask = self._dropout_mask(H.shape)
                    H = H * mask
            
            layer_outputs.append(H)
        
        return H, layer_outputs
    
    def _compute_link_score(self, embeddings: np.ndarray, src: np.ndarray, dst: np.ndarray) -> np.ndarray:
        """Compute link prediction scores."""
        src_emb = embeddings[src]
        dst_emb = embeddings[dst]
        
        # Inner product
        scores = np.sum(src_emb * dst_emb, axis=1)
        return scores
    
    def _sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid function with clipping for numerical stability."""
        return 1.0 / (1.0 + np.exp(-np.clip(x, -20, 20)))
    
    def _binary_cross_entropy(self, pred: np.ndarray, target: np.ndarray) -> float:
        """Compute binary cross entropy loss."""
        eps = 1e-10
        pred = np.clip(pred, eps, 1 - eps)
        loss = -np.mean(target * np.log(pred) + (1 - target) * np.log(1 - pred))
        return loss
    
    def _train_epoch(self, X: np.ndarray, train_edges: np.ndarray) -> float:
        """Train one epoch."""
        # Get edge data
        src = train_edges[:, 0].astype(int)
        dst = train_edges[:, 1].astype(int)
        labels = train_edges[:, 2].astype(np.float32)
        
        # Forward pass
        embeddings, layer_outputs = self._forward(X, training=True)
        
        # Compute scores
        scores = self._compute_link_score(embeddings, src, dst)
        probs = self._sigmoid(scores)
        
        # Compute loss
        loss = self._binary_cross_entropy(probs, labels)
        
        # Backward pass (simplified gradient computation)
        # Gradient of BCE w.r.t. scores
        grad_scores = (probs - labels) / len(labels)
        
        # Gradient w.r.t. embeddings (from link prediction)
        grad_embeddings = np.zeros_like(embeddings)
        np.add.at(grad_embeddings, src, grad_scores[:, np.newaxis] * embeddings[dst])
        np.add.at(grad_embeddings, dst, grad_scores[:, np.newaxis] * embeddings[src])
        
        # Backpropagate through GCN layers
        grad_H = grad_embeddings
        
        for i in range(len(self.weights) - 1, -1, -1):
            W = self.weights[i]
            H_prev = layer_outputs[i]
            
            # Gradient w.r.t. weights
            grad_W = H_prev.T @ (self.adj_norm.T @ grad_H)
            
            # Update weights
            self.weights[i] -= self.learning_rate * grad_W
            
            # Gradient w.r.t. previous layer (except for first layer)
            if i > 0:
                grad_H = self.adj_norm.T @ grad_H @ W.T
                
                # ReLU derivative
                grad_H = grad_H * self._relu_derivative(layer_outputs[i])
        
        return loss
    
    def _validate(self, X: np.ndarray, val_edges: np.ndarray) -> float:
        """Compute validation loss."""
        if len(val_edges) == 0:
            return 0.0
        
        # Forward pass (no training)
        embeddings, _ = self._forward(X, training=False)
        
        # Get edge data
        src = val_edges[:, 0].astype(int)
        dst = val_edges[:, 1].astype(int)
        labels = val_edges[:, 2].astype(np.float32)
        
        # Compute scores
        scores = self._compute_link_score(embeddings, src, dst)
        probs = self._sigmoid(scores)
        
        # Compute loss
        loss = self._binary_cross_entropy(probs, labels)
        
        return loss
    
    def train(
        self,
        node_index: Dict[str, Dict[str, int]],
        edge_index: np.ndarray,
        train_edges: np.ndarray,
        val_edges: np.ndarray,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Train GCN embeddings."""
        start_time = time.time()
        
        # Calculate number of nodes
        all_nodes = set()
        for edge in edge_index:
            all_nodes.add(int(edge[0]))
            all_nodes.add(int(edge[1]))
        self.num_nodes = max(all_nodes) + 1 if all_nodes else 0
        
        if self.num_nodes == 0:
            raise ValueError("No nodes found in graph")
        
        # Build normalized adjacency matrix from training edges
        self.adj_norm = self._build_adjacency(train_edges, self.num_nodes)
        
        # Initialize node features (one-hot or random)
        # Using random features as one-hot would be too large
        input_dim = min(self.num_nodes, 128)  # Limit input dimension
        X = np.random.randn(self.num_nodes, input_dim).astype(np.float32) * 0.01
        
        # Initialize weights
        self._init_weights(input_dim)
        
        # Training loop
        best_val_loss = float('inf')
        patience = 20
        patience_counter = 0
        
        for epoch in range(self.epochs):
            # Train
            train_loss = self._train_epoch(X, train_edges)
            
            # Validate
            val_loss = self._validate(X, val_edges)
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Save best embeddings
                self.embeddings, _ = self._forward(X, training=False)
            else:
                patience_counter += 1
            
            # Report progress
            self._report_progress(epoch + 1, train_loss, val_loss)
            
            if patience_counter >= patience:
                break
        
        # Get final embeddings if not set by early stopping
        if self.embeddings is None:
            self.embeddings, _ = self._forward(X, training=False)
        
        training_time = time.time() - start_time
        
        # Prepare metadata
        metadata = {
            "algorithm": "gcn",
            "embedding_dim": self.embedding_dim,
            "epochs": epoch + 1,  # Actual epochs trained
            "max_epochs": self.epochs,
            "learning_rate": self.learning_rate,
            "random_seed": self.random_seed,
            "hidden_channels": self.hidden_channels,
            "num_layers": self.num_layers,
            "dropout": self.dropout,
            "num_nodes": self.num_nodes,
            "input_dim": input_dim,
            "training_time_seconds": training_time,
            "final_train_loss": self.history["train_losses"][-1] if self.history["train_losses"] else None,
            "final_val_loss": self.history["val_losses"][-1] if self.history["val_losses"] else None,
            "best_val_loss": best_val_loss,
        }
        
        return self.embeddings, metadata
    
    def save(self, embedding_path: str, model_path: Optional[str] = None) -> None:
        """Save trained embeddings and model weights."""
        if self.embeddings is None:
            raise ValueError("No embeddings to save. Train first.")
        
        # Save embeddings
        np.save(embedding_path, self.embeddings)
        
        # Save model (weights and metadata)
        if model_path:
            model_data = {
                "embedding_dim": self.embedding_dim,
                "epochs": self.epochs,
                "learning_rate": self.learning_rate,
                "random_seed": self.random_seed,
                "hidden_channels": self.hidden_channels,
                "num_layers": self.num_layers,
                "dropout": self.dropout,
                "num_nodes": self.num_nodes,
                "weights_shapes": [w.shape for w in self.weights],
                "history": self.history,
            }
            
            # Save weights as separate files
            weights_path = model_path.replace(".json", "_weights.npz")
            np.savez(weights_path, *self.weights)
            model_data["weights_path"] = weights_path
            
            with open(model_path, "w") as f:
                json.dump(model_data, f, indent=2)
    
    def load(self, embedding_path: str, model_path: Optional[str] = None) -> np.ndarray:
        """Load trained embeddings and model weights."""
        self.embeddings = np.load(embedding_path)
        
        if model_path and os.path.exists(model_path):
            with open(model_path, "r") as f:
                model_data = json.load(f)
                
                self.embedding_dim = model_data.get("embedding_dim", self.embedding_dim)
                self.hidden_channels = model_data.get("hidden_channels", self.hidden_channels)
                self.num_layers = model_data.get("num_layers", self.num_layers)
                self.dropout = model_data.get("dropout", self.dropout)
                self.num_nodes = model_data.get("num_nodes", len(self.embeddings))
                self.history = model_data.get("history", self.history)
                
                # Load weights
                weights_path = model_data.get("weights_path")
                if weights_path and os.path.exists(weights_path):
                    weights_data = np.load(weights_path)
                    self.weights = [weights_data[f"arr_{i}"] for i in range(len(weights_data.files))]
        
        return self.embeddings
