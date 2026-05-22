"""Random Forest classifier implementation."""
from typing import Optional, Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier as SKRandomForest

from app.algorithms.classifiers.base import BaseClassifier


class RandomForestClassifier(BaseClassifier):
    """Random Forest classifier for drug-disease association prediction."""
    
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: Optional[int] = None,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        class_weight: Optional[str] = "balanced",
        random_seed: int = 42,
        **kwargs
    ):
        """
        Initialize Random Forest classifier.
        
        Args:
            n_estimators: Number of trees in the forest
            max_depth: Maximum depth of trees (None for unlimited)
            min_samples_split: Minimum samples required to split a node
            min_samples_leaf: Minimum samples required in a leaf
            class_weight: Class weight strategy ('balanced' or None)
            random_seed: Random seed for reproducibility
        """
        super().__init__(random_seed=random_seed)
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.class_weight = class_weight
    
    def _create_model(self) -> SKRandomForest:
        """Create sklearn RandomForestClassifier."""
        return SKRandomForest(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
            class_weight=self.class_weight,
            random_state=self.random_seed,
            n_jobs=-1,  # Use all cores
        )
    
    def _get_feature_importance(self) -> Optional[np.ndarray]:
        """Get feature importance from fitted model."""
        if self.model is not None and hasattr(self.model, "feature_importances_"):
            return self.model.feature_importances_
        return None
    
    def get_params(self) -> dict:
        """Get classifier parameters."""
        return {
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "min_samples_split": self.min_samples_split,
            "min_samples_leaf": self.min_samples_leaf,
            "class_weight": self.class_weight,
            "random_seed": self.random_seed,
        }
