"""Contrastive learning trainer for embedding model with hard negative mining."""
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)


class ContrastiveLoss(nn.Module):
    """InfoNCE contrastive loss."""
    
    def __init__(self, temperature: float = 0.07):
        """
        Initialize contrastive loss.
        
        Args:
            temperature: Temperature parameter for softmax
        """
        super().__init__()
        self.temperature = temperature
    
    def forward(self, anchor: torch.Tensor, positive: torch.Tensor, negatives: torch.Tensor) -> torch.Tensor:
        """
        Compute InfoNCE loss.
        
        Args:
            anchor: Anchor embeddings (batch_size, dim)
            positive: Positive (augmented) embeddings (batch_size, dim)
            negatives: Negative embeddings (batch_size, num_negatives, dim)
        
        Returns:
            Loss value
        """
        batch_size = anchor.size(0)
        
        # Normalize embeddings
        anchor = nn.functional.normalize(anchor, p=2, dim=1)
        positive = nn.functional.normalize(positive, p=2, dim=1)
        negatives = nn.functional.normalize(negatives, p=2, dim=2)
        
        # Compute positive similarity
        pos_sim = torch.sum(anchor * positive, dim=1) / self.temperature  # (batch_size,)
        
        # Compute negative similarities
        neg_sim = torch.bmm(
            anchor.unsqueeze(1),  # (batch_size, 1, dim)
            negatives.transpose(1, 2)  # (batch_size, dim, num_negatives)
        ).squeeze(1) / self.temperature  # (batch_size, num_negatives)
        
        # Concatenate positive and negatives
        logits = torch.cat([pos_sim.unsqueeze(1), neg_sim], dim=1)  # (batch_size, 1 + num_negatives)
        
        # Labels: 0 is positive
        labels = torch.zeros(batch_size, dtype=torch.long, device=anchor.device)
        
        # Cross-entropy loss
        loss = nn.functional.cross_entropy(logits, labels)
        
        return loss


class HardNegativeMiner:
    """Hard negative mining for contrastive learning."""
    
    def __init__(self, num_hard_negatives: int = 5, similarity_threshold: float = 0.5):
        """
        Initialize hard negative miner.
        
        Args:
            num_hard_negatives: Number of hard negatives to mine
            similarity_threshold: Threshold for considering a negative as "hard"
        """
        self.num_hard_negatives = num_hard_negatives
        self.similarity_threshold = similarity_threshold
    
    def mine_hard_negatives(
        self,
        anchor: np.ndarray,
        candidate_negatives: np.ndarray,
        num_negatives: int = 10
    ) -> np.ndarray:
        """
        Mine hard negatives from candidate pool.
        
        Hard negatives are those that are similar to the anchor but not the same.
        This makes the contrastive learning task more challenging and effective.
        
        Args:
            anchor: Anchor embedding (dim,)
            candidate_negatives: Pool of candidate negative embeddings (N, dim)
            num_negatives: Number of negatives to return
        
        Returns:
            Hard negative embeddings (num_negatives, dim)
        """
        if len(candidate_negatives) == 0:
            # Return random negatives if no candidates
            return np.random.randn(num_negatives, anchor.shape[0]).astype(np.float32)
        
        # Compute similarities
        anchor_norm = anchor / (np.linalg.norm(anchor) + 1e-8)
        candidate_norms = candidate_negatives / (np.linalg.norm(candidate_negatives, axis=1, keepdims=True) + 1e-8)
        
        similarities = np.dot(candidate_norms, anchor_norm)
        
        # Hard negatives are those with similarity above threshold but not too high
        # (too high might be false negatives)
        hard_mask = (similarities > self.similarity_threshold) & (similarities < 0.95)
        
        if np.sum(hard_mask) > 0:
            # Select hard negatives
            hard_negatives = candidate_negatives[hard_mask]
            # Sort by similarity (descending) and take top k
            hard_similarities = similarities[hard_mask]
            sorted_indices = np.argsort(hard_similarities)[::-1]
            hard_negatives = hard_negatives[sorted_indices[:num_negatives]]
            
            # Pad if needed
            if len(hard_negatives) < num_negatives:
                # Fill with random negatives
                remaining = num_negatives - len(hard_negatives)
                random_negatives = candidate_negatives[
                    np.random.choice(len(candidate_negatives), remaining, replace=False)
                ]
                hard_negatives = np.vstack([hard_negatives, random_negatives])
        else:
            # No hard negatives found, use random sampling
            if len(candidate_negatives) >= num_negatives:
                indices = np.random.choice(len(candidate_negatives), num_negatives, replace=False)
                hard_negatives = candidate_negatives[indices]
            else:
                # Repeat if not enough candidates
                indices = np.random.choice(len(candidate_negatives), num_negatives, replace=True)
                hard_negatives = candidate_negatives[indices]
        
        return hard_negatives.astype(np.float32)


class EmbeddingTrainer:
    """Trains embedding model with contrastive learning and hard negative mining."""
    
    def __init__(
        self,
        embedding_dim: int = 512,
        device: Optional[str] = None,
        use_hard_negatives: bool = True,
        num_hard_negatives: int = 5
    ):
        """
        Initialize trainer.
        
        Args:
            embedding_dim: Embedding dimension
            device: torch device
            use_hard_negatives: Whether to use hard negative mining
            num_hard_negatives: Number of hard negatives per anchor
        """
        self.embedding_dim = embedding_dim
        self.use_hard_negatives = use_hard_negatives
        
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        # Initialize hard negative miner
        if use_hard_negatives:
            self.hard_negative_miner = HardNegativeMiner(
                num_hard_negatives=num_hard_negatives
            )
            logger.info(f"Hard negative mining enabled with {num_hard_negatives} hard negatives")
        else:
            self.hard_negative_miner = None
        
        # Simple projection head for training
        self.projection_head = nn.Sequential(
            nn.Linear(embedding_dim, embedding_dim),
            nn.ReLU(),
            nn.Linear(embedding_dim, embedding_dim)
        ).to(self.device)
        
        self.criterion = ContrastiveLoss(temperature=0.07)
        self.optimizer = optim.Adam(self.projection_head.parameters(), lr=1e-4)
    
    def train_epoch(
        self,
        anchors: np.ndarray,
        positives: np.ndarray,
        negatives: np.ndarray,
        candidate_pool: Optional[np.ndarray] = None,
        batch_size: int = 32
    ) -> float:
        """
        Train for one epoch with optional hard negative mining.
        
        Args:
            anchors: Anchor embeddings (N, dim)
            positives: Positive embeddings (N, dim)
            negatives: Negative embeddings (N, num_neg, dim) - used if hard mining disabled
            candidate_pool: Pool of candidate negatives for hard mining (M, dim)
            batch_size: Batch size
        
        Returns:
            Average loss
        """
        self.projection_head.train()
        
        num_samples = len(anchors)
        total_loss = 0.0
        num_batches = 0
        
        for i in range(0, num_samples, batch_size):
            end_idx = min(i + batch_size, num_samples)
            
            # Get batch
            batch_anchors = torch.from_numpy(anchors[i:end_idx]).float().to(self.device)
            batch_positives = torch.from_numpy(positives[i:end_idx]).float().to(self.device)
            
            # Get negatives (with hard mining if enabled)
            if self.use_hard_negatives and candidate_pool is not None:
                # Mine hard negatives for each anchor in batch
                batch_hard_negatives = []
                for anchor in anchors[i:end_idx]:
                    hard_negs = self.hard_negative_miner.mine_hard_negatives(
                        anchor, candidate_pool, num_negatives=10
                    )
                    batch_hard_negatives.append(hard_negs)
                batch_negatives = np.array(batch_hard_negatives)
            else:
                # Use provided negatives
                batch_negatives = negatives[i:end_idx]
            
            batch_negatives = torch.from_numpy(batch_negatives).float().to(self.device)
            
            # Project
            proj_anchors = self.projection_head(batch_anchors)
            proj_positives = self.projection_head(batch_positives)
            proj_negatives = self.projection_head(batch_negatives)
            
            # Compute loss
            loss = self.criterion(proj_anchors, proj_positives, proj_negatives.unsqueeze(1))
            
            # Backward
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        
        return total_loss / num_batches if num_batches > 0 else 0.0
    
    def save_model(self, model_path: Path):
        """Save trained model."""
        model_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'projection_head': self.projection_head.state_dict(),
            'embedding_dim': self.embedding_dim,
            'use_hard_negatives': self.use_hard_negatives
        }, model_path)
        logger.info(f"Saved model to {model_path}")
    
    def load_model(self, model_path: Path):
        """Load trained model."""
        checkpoint = torch.load(model_path, map_location=self.device)
        self.projection_head.load_state_dict(checkpoint['projection_head'])
        self.embedding_dim = checkpoint.get('embedding_dim', 512)
        self.use_hard_negatives = checkpoint.get('use_hard_negatives', True)
        logger.info(f"Loaded model from {model_path}")
