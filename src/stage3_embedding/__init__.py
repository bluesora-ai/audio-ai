"""Stage 3: Embedding Generation."""
from .embedding_generator import EmbeddingGenerator
from .augmentation import AudioAugmentation

try:
    from .contrastive_trainer import EmbeddingTrainer, ContrastiveLoss
    __all__ = ["EmbeddingGenerator", "AudioAugmentation", "EmbeddingTrainer", "ContrastiveLoss"]
except ImportError:
    __all__ = ["EmbeddingGenerator", "AudioAugmentation"]
