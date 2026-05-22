"""Base classifier and feature combiner classes."""
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, List, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split, StratifiedKFold


class FeatureCombiner:
    """Combine drug and disease embeddings into edge features."""
    
    METHODS = ["concat", "hadamard", "l1", "l2", "average"]
    
    def __init__(self, method: str = "concat"):
        """
        Initialize feature combiner.
        
        Args:
            method: Feature combination method. One of:
                - 'concat': Concatenate vectors [u; v]
                - 'hadamard': Element-wise product u * v
                - 'l1': Absolute difference |u - v|
                - 'l2': Squared difference (u - v)^2
                - 'average': Element-wise average (u + v) / 2
        """
        if method not in self.METHODS:
            raise ValueError(f"Unknown method: {method}. Must be one of {self.METHODS}")
        self.method = method
    
    def combine(self, emb1: np.ndarray, emb2: np.ndarray) -> np.ndarray:
        """
        Combine two embedding vectors.
        
        Args:
            emb1: First embedding vector (e.g., drug embedding)
            emb2: Second embedding vector (e.g., disease embedding)
            
        Returns:
            Combined feature vector
        """
        if self.method == "concat":
            return np.concatenate([emb1, emb2], axis=-1)
        elif self.method == "hadamard":
            return emb1 * emb2
        elif self.method == "l1":
            return np.abs(emb1 - emb2)
        elif self.method == "l2":
            return (emb1 - emb2) ** 2
        elif self.method == "average":
            return (emb1 + emb2) / 2
        else:
            raise ValueError(f"Unknown method: {self.method}")
    
    def combine_batch(self, emb1: np.ndarray, emb2: np.ndarray) -> np.ndarray:
        """
        Combine batches of embedding vectors.
        
        Args:
            emb1: First embedding array of shape (N, dim)
            emb2: Second embedding array of shape (N, dim)
            
        Returns:
            Combined feature array
        """
        if len(emb1.shape) == 1:
            emb1 = emb1.reshape(1, -1)
        if len(emb2.shape) == 1:
            emb2 = emb2.reshape(1, -1)
        
        return self.combine(emb1, emb2)
    
    def get_output_dim(self, input_dim: int) -> int:
        """Get output dimension for given input dimension."""
        if self.method == "concat":
            return input_dim * 2
        else:
            return input_dim


class BaseClassifier(ABC):
    """Base class for classifiers."""
    
    def __init__(
        self,
        random_seed: int = 42,
        **params
    ):
        """
        Initialize classifier.
        
        Args:
            random_seed: Random seed for reproducibility
            **params: Classifier-specific parameters
        """
        self.random_seed = random_seed
        self.params = params
        self.model = None
        self.is_fitted = False
        self.training_time = 0.0
        self._feature_importance = None
        self._history = {}
    
    @abstractmethod
    def _create_model(self) -> Any:
        """Create the underlying model."""
        pass
    
    @abstractmethod
    def _get_feature_importance(self) -> Optional[np.ndarray]:
        """Get feature importance from fitted model."""
        pass
    
    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
    ) -> "BaseClassifier":
        """
        Fit the classifier.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
            
        Returns:
            self
        """
        self.model = self._create_model()
        
        start_time = time.time()
        self.model.fit(X_train, y_train)
        self.training_time = time.time() - start_time
        
        self.is_fitted = True
        self._feature_importance = self._get_feature_importance()
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        if not self.is_fitted:
            raise RuntimeError("Model has not been fitted")
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities."""
        if not self.is_fitted:
            raise RuntimeError("Model has not been fitted")
        return self.model.predict_proba(X)
    
    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray,
    ) -> Dict[str, float]:
        """
        Evaluate model on test data.
        
        Args:
            X_test: Test features
            y_test: Test labels
            
        Returns:
            Dictionary of evaluation metrics
        """
        y_pred = self.predict(X_test)
        y_proba = self.predict_proba(X_test)[:, 1]
        
        metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
            "auc_roc": float(roc_auc_score(y_test, y_proba)),
            "auc_pr": float(average_precision_score(y_test, y_proba)),
        }
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        if cm.shape == (2, 2):
            metrics["confusion_matrix"] = {
                "tn": int(cm[0, 0]),
                "fp": int(cm[0, 1]),
                "fn": int(cm[1, 0]),
                "tp": int(cm[1, 1]),
            }
        
        return metrics
    
    def train_and_evaluate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
        k_fold: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Train and evaluate the classifier.
        
        Args:
            X: Features
            y: Labels  
            test_size: Proportion of data to use for testing
            k_fold: Number of folds for cross-validation (None to disable)
            
        Returns:
            Dictionary with metrics and metadata
        """
        result = {
            "num_samples": len(y),
            "num_features": X.shape[1],
            "num_positive": int(np.sum(y)),
            "num_negative": int(np.sum(1 - y)),
        }
        
        if k_fold is not None and k_fold >= 2:
            # K-fold cross-validation
            kfold_result = self._kfold_cv(X, y, k_fold)
            result["kfold_metrics"] = kfold_result
            
            # Also train final model on full training set
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=self.random_seed, stratify=y
            )
        else:
            # Simple train/test split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=self.random_seed, stratify=y
            )
        
        result["num_train_samples"] = len(y_train)
        result["num_test_samples"] = len(y_test)
        
        # Fit on training data
        self.fit(X_train, y_train)
        result["training_time_seconds"] = self.training_time
        
        # Evaluate on test data
        metrics = self.evaluate(X_test, y_test)
        result.update(metrics)
        
        # Feature importance
        if self._feature_importance is not None:
            result["feature_importance"] = self._feature_importance.tolist()
        
        return result
    
    def _kfold_cv(
        self,
        X: np.ndarray,
        y: np.ndarray,
        k: int,
    ) -> Dict[str, Any]:
        """
        Perform k-fold cross-validation.
        
        Args:
            X: Features
            y: Labels
            k: Number of folds
            
        Returns:
            Dictionary with fold metrics, mean, and std
        """
        skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=self.random_seed)
        
        fold_metrics = []
        for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X, y)):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            # Create a fresh model for each fold
            model = self._create_model()
            model.fit(X_train, y_train)
            
            y_pred = model.predict(X_val)
            y_proba = model.predict_proba(X_val)[:, 1]
            
            metrics = {
                "fold": fold_idx + 1,
                "accuracy": float(accuracy_score(y_val, y_pred)),
                "precision": float(precision_score(y_val, y_pred, zero_division=0)),
                "recall": float(recall_score(y_val, y_pred, zero_division=0)),
                "f1_score": float(f1_score(y_val, y_pred, zero_division=0)),
                "auc_roc": float(roc_auc_score(y_val, y_proba)),
                "auc_pr": float(average_precision_score(y_val, y_proba)),
            }
            fold_metrics.append(metrics)
        
        # Calculate mean and std
        metric_keys = ["accuracy", "precision", "recall", "f1_score", "auc_roc", "auc_pr"]
        mean_metrics = {}
        std_metrics = {}
        
        for key in metric_keys:
            values = [m[key] for m in fold_metrics]
            mean_metrics[key] = float(np.mean(values))
            std_metrics[key] = float(np.std(values))
        
        return {
            "fold_metrics": fold_metrics,
            "mean_metrics": mean_metrics,
            "std_metrics": std_metrics,
        }
    
    def get_feature_importance(self) -> Optional[np.ndarray]:
        """Get feature importance array."""
        return self._feature_importance
    
    def get_history(self) -> Dict[str, Any]:
        """Get training history."""
        return self._history
