"""Node2Vec embedding algorithm implementation."""
import os
import json
import time
from typing import Dict, Any, Optional, Tuple, List, Callable
import numpy as np
from collections import defaultdict

from .base import BaseEmbeddingTrainer


class Node2VecTrainer(BaseEmbeddingTrainer):
    """
    Node2Vec embedding trainer using random walks and skip-gram.
    
    Based on: Grover & Leskovec, "node2vec: Scalable Feature Learning for Networks", KDD 2016
    """
    
    def __init__(
        self,
        embedding_dim: int = 64,
        epochs: int = 100,
        learning_rate: float = 0.01,
        random_seed: int = 42,
        walk_length: int = 80,
        num_walks: int = 10,
        p: float = 1.0,
        q: float = 1.0,
        window_size: int = 5,
        progress_callback: Optional[Callable[[int, float, Optional[float]], None]] = None,
    ):
        """
        Initialize Node2Vec trainer.
        
        Args:
            embedding_dim: Dimension of embeddings
            epochs: Number of training epochs
            learning_rate: Learning rate for skip-gram
            random_seed: Random seed for reproducibility
            walk_length: Length of each random walk
            num_walks: Number of random walks per node
            p: Return parameter (controls likelihood of revisiting a node)
            q: In-out parameter (controls search behavior - BFS vs DFS)
            window_size: Context window size for skip-gram
            progress_callback: Callback for progress updates
        """
        super().__init__(embedding_dim, epochs, learning_rate, random_seed, progress_callback)
        
        self.walk_length = walk_length
        self.num_walks = num_walks
        self.p = p
        self.q = q
        self.window_size = window_size
        
        # Model parameters
        self.embeddings: Optional[np.ndarray] = None
        self.num_nodes: int = 0
        self.graph: Dict[int, List[int]] = {}
    
    def _build_graph(self, edge_index: np.ndarray) -> Dict[int, List[int]]:
        """Build adjacency list from edge index (only positive edges)."""
        graph = defaultdict(list)
        
        for edge in edge_index:
            src, dst, label = int(edge[0]), int(edge[1]), int(edge[2])
            if label == 1:  # Only use positive edges for random walks
                graph[src].append(dst)
                graph[dst].append(src)  # Undirected graph
        
        return dict(graph)
    
    def _compute_transition_probs(self) -> Dict[Tuple[int, int], np.ndarray]:
        """Compute transition probabilities for biased random walks."""
        alias_nodes = {}
        alias_edges = {}
        
        # Compute probabilities for first step (uniform)
        for node in self.graph:
            neighbors = self.graph[node]
            if neighbors:
                probs = np.ones(len(neighbors)) / len(neighbors)
                alias_nodes[node] = self._create_alias_table(probs)
        
        # Compute probabilities for subsequent steps (biased by p, q)
        for src in self.graph:
            for dst in self.graph.get(src, []):
                probs = []
                for dst_neighbor in self.graph.get(dst, []):
                    if dst_neighbor == src:
                        # Return to source: probability 1/p
                        probs.append(1.0 / self.p)
                    elif dst_neighbor in self.graph.get(src, []):
                        # Common neighbor: probability 1
                        probs.append(1.0)
                    else:
                        # Far from source: probability 1/q
                        probs.append(1.0 / self.q)
                
                if probs:
                    probs = np.array(probs)
                    probs = probs / probs.sum()
                    alias_edges[(src, dst)] = self._create_alias_table(probs)
        
        return alias_nodes, alias_edges
    
    def _create_alias_table(self, probs: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create alias table for efficient sampling."""
        n = len(probs)
        alias = np.zeros(n, dtype=np.int32)
        prob = np.zeros(n)
        
        # Normalize probabilities
        probs = probs * n
        
        # Separate into small and large
        smaller = []
        larger = []
        
        for i, p in enumerate(probs):
            if p < 1.0:
                smaller.append(i)
            else:
                larger.append(i)
        
        # Build alias table
        while smaller and larger:
            small = smaller.pop()
            large = larger.pop()
            
            prob[small] = probs[small]
            alias[small] = large
            
            probs[large] = probs[large] + probs[small] - 1.0
            
            if probs[large] < 1.0:
                smaller.append(large)
            else:
                larger.append(large)
        
        while larger:
            large = larger.pop()
            prob[large] = 1.0
        
        while smaller:
            small = smaller.pop()
            prob[small] = 1.0
        
        return prob, alias
    
    def _alias_sample(self, prob: np.ndarray, alias: np.ndarray) -> int:
        """Sample from alias table."""
        n = len(prob)
        i = np.random.randint(n)
        if np.random.random() < prob[i]:
            return i
        return alias[i]
    
    def _random_walk(self, start_node: int, alias_nodes: Dict, alias_edges: Dict) -> List[int]:
        """Perform a single random walk starting from start_node."""
        walk = [start_node]
        
        if start_node not in self.graph or not self.graph[start_node]:
            return walk
        
        # First step (uniform)
        if start_node in alias_nodes:
            prob, alias = alias_nodes[start_node]
            next_idx = self._alias_sample(prob, alias)
            neighbors = self.graph[start_node]
            if next_idx < len(neighbors):
                walk.append(neighbors[next_idx])
        
        # Subsequent steps (biased)
        while len(walk) < self.walk_length:
            cur = walk[-1]
            if cur not in self.graph or not self.graph[cur]:
                break
            
            prev = walk[-2] if len(walk) > 1 else walk[-1]
            
            if (prev, cur) in alias_edges:
                prob, alias = alias_edges[(prev, cur)]
                next_idx = self._alias_sample(prob, alias)
                neighbors = self.graph[cur]
                if next_idx < len(neighbors):
                    walk.append(neighbors[next_idx])
                else:
                    break
            else:
                # Fallback to uniform
                neighbors = self.graph[cur]
                walk.append(np.random.choice(neighbors))
        
        return walk
    
    def _generate_walks(self, alias_nodes: Dict, alias_edges: Dict) -> List[List[int]]:
        """Generate random walks for all nodes."""
        walks = []
        nodes = list(self.graph.keys())
        
        for _ in range(self.num_walks):
            np.random.shuffle(nodes)
            for node in nodes:
                walk = self._random_walk(node, alias_nodes, alias_edges)
                if len(walk) > 1:
                    walks.append(walk)
        
        return walks
    
    def _train_skip_gram(self, walks: List[List[int]], val_edges: np.ndarray) -> None:
        """Train skip-gram model on random walks."""
        # Initialize embeddings
        self.embeddings = np.random.randn(self.num_nodes, self.embedding_dim) * 0.01
        context_embeddings = np.random.randn(self.num_nodes, self.embedding_dim) * 0.01
        
        # Build training pairs
        pairs = []
        for walk in walks:
            for i, center in enumerate(walk):
                context_start = max(0, i - self.window_size)
                context_end = min(len(walk), i + self.window_size + 1)
                
                for j in range(context_start, context_end):
                    if i != j:
                        pairs.append((center, walk[j]))
        
        if not pairs:
            return
        
        pairs = np.array(pairs)
        n_pairs = len(pairs)
        batch_size = min(1024, n_pairs)
        
        # Training loop
        for epoch in range(self.epochs):
            # Shuffle pairs
            indices = np.random.permutation(n_pairs)
            total_loss = 0.0
            n_batches = 0
            
            for batch_start in range(0, n_pairs, batch_size):
                batch_indices = indices[batch_start:batch_start + batch_size]
                batch = pairs[batch_indices]
                
                centers = batch[:, 0]
                contexts = batch[:, 1]
                
                # Forward pass
                center_emb = self.embeddings[centers]  # (batch, dim)
                context_emb = context_embeddings[contexts]  # (batch, dim)
                
                # Positive score
                pos_score = np.sum(center_emb * context_emb, axis=1)  # (batch,)
                pos_prob = 1.0 / (1.0 + np.exp(-np.clip(pos_score, -20, 20)))
                
                # Negative sampling
                neg_samples = np.random.randint(0, self.num_nodes, size=(len(batch), 5))
                neg_emb = context_embeddings[neg_samples]  # (batch, 5, dim)
                neg_score = np.sum(center_emb[:, np.newaxis, :] * neg_emb, axis=2)  # (batch, 5)
                neg_prob = 1.0 / (1.0 + np.exp(-np.clip(neg_score, -20, 20)))
                
                # Loss
                eps = 1e-10
                loss = -np.mean(np.log(pos_prob + eps)) - np.mean(np.log(1 - neg_prob + eps))
                total_loss += loss
                n_batches += 1
                
                # Backward pass
                grad_pos = pos_prob - 1  # (batch,)
                grad_neg = neg_prob  # (batch, 5)
                
                # Update center embeddings
                grad_center = grad_pos[:, np.newaxis] * context_emb
                grad_center += np.sum(grad_neg[:, :, np.newaxis] * neg_emb, axis=1)
                
                np.add.at(self.embeddings, centers, -self.learning_rate * grad_center)
                
                # Update context embeddings
                grad_context = grad_pos[:, np.newaxis] * center_emb
                np.add.at(context_embeddings, contexts, -self.learning_rate * grad_context)
                
                # Update negative embeddings
                for i in range(5):
                    grad_neg_i = grad_neg[:, i:i+1] * center_emb
                    np.add.at(context_embeddings, neg_samples[:, i], -self.learning_rate * grad_neg_i)
            
            avg_loss = total_loss / max(n_batches, 1)
            
            # Compute validation loss (link prediction)
            val_loss = self._compute_val_loss(val_edges)
            
            # Report progress
            self._report_progress(epoch + 1, avg_loss, val_loss)
    
    def _compute_val_loss(self, val_edges: np.ndarray) -> float:
        """Compute validation loss using link prediction."""
        if self.embeddings is None or len(val_edges) == 0:
            return 0.0
        
        total_loss = 0.0
        n_edges = len(val_edges)
        
        for edge in val_edges:
            src, dst, label = int(edge[0]), int(edge[1]), int(edge[2])
            
            if src < self.num_nodes and dst < self.num_nodes:
                src_emb = self.embeddings[src]
                dst_emb = self.embeddings[dst]
                
                # Cosine similarity
                score = np.dot(src_emb, dst_emb) / (np.linalg.norm(src_emb) * np.linalg.norm(dst_emb) + 1e-10)
                
                # Binary cross entropy
                prob = 1.0 / (1.0 + np.exp(-np.clip(score * 5, -20, 20)))  # Scale score
                eps = 1e-10
                if label == 1:
                    total_loss -= np.log(prob + eps)
                else:
                    total_loss -= np.log(1 - prob + eps)
        
        return total_loss / max(n_edges, 1)
    
    def train(
        self,
        node_index: Dict[str, Dict[str, int]],
        edge_index: np.ndarray,
        train_edges: np.ndarray,
        val_edges: np.ndarray,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Train Node2Vec embeddings."""
        start_time = time.time()
        
        # Build graph from training edges
        self.graph = self._build_graph(train_edges)
        
        # Calculate number of nodes
        all_nodes = set()
        for edge in edge_index:
            all_nodes.add(int(edge[0]))
            all_nodes.add(int(edge[1]))
        self.num_nodes = max(all_nodes) + 1 if all_nodes else 0
        
        if self.num_nodes == 0:
            raise ValueError("No nodes found in graph")
        
        # Compute transition probabilities
        alias_nodes, alias_edges = self._compute_transition_probs()
        
        # Generate random walks
        walks = self._generate_walks(alias_nodes, alias_edges)
        
        if not walks:
            # Initialize random embeddings if no walks generated
            self.embeddings = np.random.randn(self.num_nodes, self.embedding_dim) * 0.01
        else:
            # Train skip-gram
            self._train_skip_gram(walks, val_edges)
        
        training_time = time.time() - start_time
        
        # Prepare metadata
        metadata = {
            "algorithm": "node2vec",
            "embedding_dim": self.embedding_dim,
            "epochs": self.epochs,
            "learning_rate": self.learning_rate,
            "random_seed": self.random_seed,
            "walk_length": self.walk_length,
            "num_walks": self.num_walks,
            "p": self.p,
            "q": self.q,
            "window_size": self.window_size,
            "num_nodes": self.num_nodes,
            "num_walks_generated": len(walks),
            "training_time_seconds": training_time,
            "final_train_loss": self.history["train_losses"][-1] if self.history["train_losses"] else None,
            "final_val_loss": self.history["val_losses"][-1] if self.history["val_losses"] else None,
        }
        
        return self.embeddings, metadata
    
    def save(self, embedding_path: str, model_path: Optional[str] = None) -> None:
        """Save trained embeddings."""
        if self.embeddings is None:
            raise ValueError("No embeddings to save. Train first.")
        
        # Save embeddings
        np.save(embedding_path, self.embeddings)
        
        # Save metadata
        if model_path:
            metadata = {
                "embedding_dim": self.embedding_dim,
                "epochs": self.epochs,
                "learning_rate": self.learning_rate,
                "random_seed": self.random_seed,
                "walk_length": self.walk_length,
                "num_walks": self.num_walks,
                "p": self.p,
                "q": self.q,
                "window_size": self.window_size,
                "num_nodes": self.num_nodes,
                "history": self.history,
            }
            with open(model_path, "w") as f:
                json.dump(metadata, f, indent=2)
    
    def load(self, embedding_path: str, model_path: Optional[str] = None) -> np.ndarray:
        """Load trained embeddings."""
        self.embeddings = np.load(embedding_path)
        
        if model_path and os.path.exists(model_path):
            with open(model_path, "r") as f:
                metadata = json.load(f)
                self.embedding_dim = metadata.get("embedding_dim", self.embedding_dim)
                self.num_nodes = metadata.get("num_nodes", len(self.embeddings))
                self.history = metadata.get("history", self.history)
        
        return self.embeddings
