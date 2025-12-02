"""Per-stem AI vs Human classifier for Milestone 2."""
import numpy as np
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, roc_auc_score
import joblib

logger = logging.getLogger(__name__)


class AIDetector:
    """Classifies audio segments as AI-generated or human."""
    
    def __init__(
        self,
        model_path: Optional[Path] = None,
        stem_type: Optional[str] = None
    ):
        """
        Initialize AI detector.
        
        Args:
            model_path: Path to saved classifier model
            stem_type: Stem type this classifier is for (vocals, drums, etc.)
        """
        self.stem_type = stem_type
        self.model = None
        self.calibrator = None
        self.feature_dim = 512  # Embedding dimension
        
        if model_path and model_path.exists():
            self.load_model(model_path)
    
    def train(
        self,
        embeddings: np.ndarray,
        labels: np.ndarray,
        stem_types: Optional[np.ndarray] = None,
        calibration: bool = True
    ):
        """
        Train classifier on embeddings.
        
        Args:
            embeddings: Embedding vectors (N, 512)
            labels: Binary labels (0=human, 1=AI) (N,)
            stem_types: Stem type for each sample (N,) - optional
            calibration: Whether to calibrate probabilities
        """
        # Filter by stem type if specified
        if self.stem_type is not None and stem_types is not None:
            mask = stem_types == self.stem_type
            embeddings = embeddings[mask]
            labels = labels[mask]
            logger.info(f"Filtered to {len(embeddings)} samples for stem_type={self.stem_type}")
        
        if len(embeddings) == 0:
            raise ValueError("No training samples after filtering")
        
        # Train Random Forest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(embeddings, labels)
        
        # Calibrate if requested
        if calibration:
            self.calibrator = CalibratedClassifierCV(
                self.model,
                method='isotonic',
                cv=5
            )
            self.calibrator.fit(embeddings, labels)
            logger.info("Classifier calibrated")
        
        logger.info(f"Trained classifier on {len(embeddings)} samples")
    
    def predict(
        self,
        embeddings: np.ndarray,
        return_proba: bool = True
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Predict AI vs Human for embeddings.
        
        Args:
            embeddings: Embedding vectors (N, 512) or (512,)
            return_proba: Whether to return probabilities
        
        Returns:
            predictions: Binary predictions (0=human, 1=AI)
            probabilities: AI probabilities (if return_proba=True)
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        # Ensure 2D
        if len(embeddings.shape) == 1:
            embeddings = embeddings.reshape(1, -1)
        
        # Predict
        predictions = self.model.predict(embeddings)
        
        probabilities = None
        if return_proba:
            if self.calibrator is not None:
                probabilities = self.calibrator.predict_proba(embeddings)[:, 1]
            else:
                probabilities = self.model.predict_proba(embeddings)[:, 1]
        
        return predictions, probabilities
    
    def evaluate(
        self,
        embeddings: np.ndarray,
        labels: np.ndarray
    ) -> Dict:
        """
        Evaluate classifier performance.
        
        Args:
            embeddings: Test embeddings
            labels: True labels
        
        Returns:
            Dictionary with metrics
        """
        predictions, probabilities = self.predict(embeddings, return_proba=True)
        
        # Calculate metrics
        from sklearn.metrics import (
            precision_score, recall_score, f1_score,
            accuracy_score, roc_auc_score
        )
        
        metrics = {
            "accuracy": float(accuracy_score(labels, predictions)),
            "precision": float(precision_score(labels, predictions, zero_division=0)),
            "recall": float(recall_score(labels, predictions, zero_division=0)),
            "f1": float(f1_score(labels, predictions, zero_division=0)),
            "roc_auc": float(roc_auc_score(labels, probabilities)) if len(np.unique(labels)) > 1 else 0.0
        }
        
        return metrics
    
    def save_model(self, model_path: Path):
        """Save classifier model."""
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        save_dict = {
            "model": self.model,
            "calibrator": self.calibrator,
            "stem_type": self.stem_type,
            "feature_dim": self.feature_dim
        }
        
        joblib.dump(save_dict, model_path)
        logger.info(f"Saved classifier to {model_path}")
    
    def load_model(self, model_path: Path):
        """Load classifier model."""
        save_dict = joblib.load(model_path)
        self.model = save_dict["model"]
        self.calibrator = save_dict.get("calibrator")
        self.stem_type = save_dict.get("stem_type")
        self.feature_dim = save_dict.get("feature_dim", 512)
        logger.info(f"Loaded classifier from {model_path}")