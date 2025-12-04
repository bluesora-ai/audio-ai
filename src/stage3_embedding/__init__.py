"""Stage 3: Embedding Generation."""
from .embedding_generator import EmbeddingGenerator
from .augmentation import AudioAugmentation

# ContrastiveTrainer requires PyTorch - make it optional
try:
    from .contrastive_trainer import EmbeddingTrainer, ContrastiveLoss
    __all__ = ["EmbeddingGenerator", "AudioAugmentation", "EmbeddingTrainer", "ContrastiveLoss"]
except (ImportError, OSError):
    # PyTorch not available or DLL error - skip contrastive trainer
    __all__ = ["EmbeddingGenerator", "AudioAugmentation"]
