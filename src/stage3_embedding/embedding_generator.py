"""OpenL3 embedding generation module for Milestone 1."""
import os
import warnings
import logging

# Suppress ALL warnings BEFORE any TensorFlow imports
# This must be done first, before importing any libraries
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 3 = suppress all except errors
warnings.filterwarnings('ignore')

# Suppress TensorFlow logging completely
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('tensorflow._api.v2').setLevel(logging.ERROR)
logging.getLogger('tensorflow.python').setLevel(logging.ERROR)
logging.getLogger('keras').setLevel(logging.ERROR)

# Suppress all Python warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*tf.placeholder.*')
warnings.filterwarnings('ignore', message='.*deprecated.*')
warnings.filterwarnings('ignore', message='.*The name tf.placeholder.*')

import numpy as np
import soundfile as sf
import librosa
from pathlib import Path
from typing import List, Dict, Optional

# Try to import openl3, with fallback if not available
# Note: Catching all exceptions, not just ImportError, because TensorFlow DLL errors
# can cause various exception types when trying to import openl3
try:
    import openl3
    HAS_OPENL3 = True
except Exception as e:
    HAS_OPENL3 = False
    # OpenL3 import failed - will use fallback embeddings

logger = logging.getLogger(__name__)

if not HAS_OPENL3:
    logger.warning("openl3 not installed. Using fallback embedding method (librosa features).")


class EmbeddingGenerator:
    """Generates embeddings using OpenL3 for Milestone 1."""
    
    def __init__(
        self,
        embedding_dim: int = 512,
        sample_rate: int = 44100,
        content_type: str = "music",
        input_repr: str = "mel256"
    ):
        """
        Initialize OpenL3 embedder.
        
        Args:
            embedding_dim: Dimension of output embedding (default: 512)
            sample_rate: Target sample rate (default: 44100)
            content_type: Content type for OpenL3 ('music' or 'env')
            input_repr: Input representation ('mel256' or 'linear')
        """
        self.embedding_dim = embedding_dim
        self.sample_rate = sample_rate
        self.content_type = content_type
        self.input_repr = input_repr
        self.model_version = "openl3-v1"
        
        # Load OpenL3 model once and reuse it for better performance
        self.openl3_model = None
        if HAS_OPENL3:
            try:
                logger.info("Loading OpenL3 model (this may take a moment on first use)...")
                # Suppress stderr during model loading to hide TensorFlow warnings
                import sys
                from contextlib import redirect_stderr
                from io import StringIO
                
                # Redirect stderr to suppress TensorFlow warnings
                stderr_buffer = StringIO()
                with redirect_stderr(stderr_buffer):
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        self.openl3_model = openl3.models.load_audio_embedding_model(
                            input_repr=self.input_repr,
                            content_type=self.content_type,
                            embedding_size=self.embedding_dim
                        )
                
                logger.info("✓ OpenL3 model loaded and ready for batch processing")
            except Exception as e:
                logger.warning(f"Failed to load OpenL3 model: {e}. Will load on each call (slower).")
                self.openl3_model = None
    
    def generate_embedding(self, audio_path: Path) -> np.ndarray:
        """
        Generate embedding for a single audio file.
        
        Args:
            audio_path: Path to audio file (should be 1 second, 44.1kHz)
        
        Returns:
            Normalized embedding vector (embedding_dim,)
        """
        try:
            # Load and preprocess audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate, mono=True)
            
            # Ensure fixed length (1 second)
            target_length = int(self.sample_rate * 1.0)
            
            if len(y) < target_length:
                # Pad with zeros
                y = np.pad(y, (0, target_length - len(y)), mode='constant')
            elif len(y) > target_length:
                # Truncate
                y = y[:target_length]
            
            # Generate embedding with OpenL3 if available
            if HAS_OPENL3:
                # Use pre-loaded model if available (much faster)
                # Suppress all warnings during embedding generation
                import sys
                from contextlib import redirect_stderr
                from io import StringIO
                
                stderr_buffer = StringIO()
                with redirect_stderr(stderr_buffer):
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        emb, _ = openl3.get_audio_embedding(
                            y,
                            sr=self.sample_rate,
                            model=self.openl3_model,  # Use pre-loaded model for performance
                            input_repr=self.input_repr,
                            content_type=self.content_type,
                            embedding_size=self.embedding_dim,
                            center=True,
                            hop_size=0.1,
                            verbose=False
                        )
                
                # Average over time frames to get single vector
                if len(emb.shape) > 1:
                    emb = np.mean(emb, axis=0)
            else:
                # Fallback: Use librosa features as placeholder
                logger.warning("Using fallback embedding (openl3 not available)")
                # Extract mel spectrogram features
                mel_spec = librosa.feature.melspectrogram(
                    y=y, sr=sr, n_mels=128, fmax=8000
                )
                # Flatten and take mean
                emb = np.mean(mel_spec, axis=1)
                # Pad or truncate to target dimension
                if len(emb) > self.embedding_dim:
                    emb = emb[:self.embedding_dim]
                else:
                    emb = np.pad(emb, (0, self.embedding_dim - len(emb)), mode='constant')
            
            # Ensure correct dimension
            if len(emb) != self.embedding_dim:
                if len(emb) > self.embedding_dim:
                    emb = emb[:self.embedding_dim]
                else:
                    emb = np.pad(emb, (0, self.embedding_dim - len(emb)), mode='constant')
            
            # L2 normalize
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
            
            return emb.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Error generating embedding for {audio_path}: {e}")
            raise
    
    def generate_embeddings_batch(
        self,
        audio_paths: List[Path],
        batch_size: int = 16
    ) -> List[np.ndarray]:
        """
        Generate embeddings for multiple audio files.
        
        Args:
            audio_paths: List of paths to audio files
            batch_size: Batch size for processing (not used in OpenL3, kept for API consistency)
        
        Returns:
            List of embedding vectors
        """
        embeddings = []
        total = len(audio_paths)
        
        for i, path in enumerate(audio_paths):
            try:
                # Show progress every 10 files or at start/end
                if i % 10 == 0 or i == total - 1:
                    logger.info(f"Processing segment {i+1}/{total}...")
                
                emb = self.generate_embedding(path)
                embeddings.append(emb)
            except Exception as e:
                logger.warning(f"Failed to generate embedding for {path}: {e}")
                # Use zero vector as fallback
                embeddings.append(np.zeros(self.embedding_dim, dtype=np.float32))
        
        return embeddings
    
    def save_embedding(self, embedding: np.ndarray, output_path: Path):
        """
        Save embedding to disk as .npy file.
        
        Args:
            embedding: Embedding vector
            output_path: Path to save embedding
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(output_path, embedding)
    
    def load_embedding(self, embedding_path: Path) -> np.ndarray:
        """
        Load embedding from disk.
        
        Args:
            embedding_path: Path to embedding file
        
        Returns:
            Embedding vector
        """
        return np.load(embedding_path)