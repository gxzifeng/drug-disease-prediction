"""SVM classifier implementation."""
from typing import Optional, Any

import numpy as np
from sklearn.svm import SVC

from app.algorithms.classifiers.base import BaseClassifier


class SVMClassifier(BaseClassifier):
    """SVM classifier for drug-disease association prediction."""
    
    def __init__(
        self,
        C: float = 1.0,
        kernel: str = "rbf",
        gamma: str = "scale",
        probability: bool = True,
        class_weight: Optional[str] = "balanced",
        random_seed: int = 42,
        **kwargs
    ):
        """
        Initialize SVM classifier.
        
        Args:
            C: Regularization parameter
            kernel: Kernel type ('linear', 'rbf', 'poly', 'sigmoid')
            gamma: Kernel coefficient ('scale', 'auto', or float)
            probability: Whether to enable probability estimates
            class_weight: Class weight strategy ('balanced' or None)
            random_seed: Random seed for reproducibility
        """
        super().__init__(random_seed=random_seed)
        self.C = C
        self.kernel = kernel
        self.gamma = gamma
        self.probability = probability
        self.class_weight = class_weight
    
    def _create_model(self) -> SVC:
        """Create sklearn SVC."""
        return SVC(
            C=self.C,
            kernel=self.kernel,
            gamma=self.gamma,
            probability=self.probability,
            class_weight=self.class_weight,
            random_state=self.random_seed,
        )
    
    def _get_feature_importance(self) -> Optional[np.ndarray]:
        """Get feature importance from fitted model.
        
        Note: SVM doesn't have native feature importance. 
        For linear kernel, we can use coefficient magnitudes.
        """
        if self.model is not None and self.kernel == "linear":
            # For linear kernel, use absolute coefficient values
            if hasattr(self.model, "coef_"):
                return np.abs(self.model.coef_[0])
        return None
    
    def get_params(self) -> dict:
        """Get classifier parameters."""
        return {
            "C": self.C,
            "kernel": self.kernel,
            "gamma": self.gamma,
            "probability": self.probability,
            "class_weight": self.class_weight,
            "random_seed": self.random_seed,
        }
