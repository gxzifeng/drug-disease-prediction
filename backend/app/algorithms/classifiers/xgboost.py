"""XGBoost classifier implementation."""
from typing import Optional, Any

import numpy as np

from app.algorithms.classifiers.base import BaseClassifier

# Try to import xgboost, provide fallback
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False


class XGBoostClassifier(BaseClassifier):
    """XGBoost classifier for drug-disease association prediction."""
    
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        scale_pos_weight: Optional[float] = None,
        random_seed: int = 42,
        **kwargs
    ):
        """
        Initialize XGBoost classifier.
        
        Args:
            n_estimators: Number of boosting rounds
            max_depth: Maximum tree depth
            learning_rate: Learning rate (eta)
            subsample: Subsample ratio of training instances
            colsample_bytree: Subsample ratio of features
            scale_pos_weight: Weight for positive class (for imbalanced data)
            random_seed: Random seed for reproducibility
        """
        if not HAS_XGBOOST:
            raise ImportError(
                "XGBoost is not installed. Install it with: pip install xgboost"
            )
        
        super().__init__(random_seed=random_seed)
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.scale_pos_weight = scale_pos_weight
    
    def _create_model(self) -> "xgb.XGBClassifier":
        """Create XGBoost classifier."""
        params = {
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "learning_rate": self.learning_rate,
            "subsample": self.subsample,
            "colsample_bytree": self.colsample_bytree,
            "random_state": self.random_seed,
            "use_label_encoder": False,
            "eval_metric": "logloss",
            "n_jobs": -1,
        }
        
        if self.scale_pos_weight is not None:
            params["scale_pos_weight"] = self.scale_pos_weight
        
        return xgb.XGBClassifier(**params)
    
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
            "learning_rate": self.learning_rate,
            "subsample": self.subsample,
            "colsample_bytree": self.colsample_bytree,
            "scale_pos_weight": self.scale_pos_weight,
            "random_seed": self.random_seed,
        }
