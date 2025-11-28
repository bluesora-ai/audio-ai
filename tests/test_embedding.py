"""Tests for embedding module."""
import pytest
from pathlib import Path
import soundfile as sf
import numpy as np
from src.stage3_embedding import EmbeddingGenerator


def create_test_audio(output_path: Path, duration_sec: float = 1.0, sr: int = 44100):
    """Create a test audio file."""
    samples = int(sr * duration_sec)
    data = np.random.randn(samples).astype(np.float32) * 0.1
    sf.write(output_path, data, sr)


def test_embedding_generation(tmp_path):
    """Test embedding generation for 1-second audio."""
    test_audio = tmp_path / "test.wav"
    create_test_audio(test_audio, duration_sec=1.0)
    
    embedder = EmbeddingGenerator(embedding_dim=512)
    embedding = embedder.generate_embedding(test_audio)
    
    assert embedding.shape == (512,), f"Expected shape (512,), got {embedding.shape}"
    assert embedding.dtype == np.float32, "Embedding should be float32"
    
    # Check normalization
    norm = np.linalg.norm(embedding)
    assert abs(norm - 1.0) < 0.01, f"Embedding should be L2 normalized, got norm={norm}"


def test_embedding_batch(tmp_path):
    """Test batch embedding generation."""
    # Create multiple test files
    audio_files = []
    for i in range(3):
        test_audio = tmp_path / f"test_{i}.wav"
        create_test_audio(test_audio, duration_sec=1.0)
        audio_files.append(test_audio)
    
    embedder = EmbeddingGenerator(embedding_dim=512)
    embedding = embedder.generate_embedding(audio_files[0])
    
    # Test save/load
    embedder.save_embedding(embedding, tmp_path / "test_emb.npy")
    loaded = embedder.load_embedding(tmp_path / "test_emb.npy")
    
    assert np.allclose(embedding, loaded), "Saved and loaded embeddings should match"


def test_embedding_short_audio(tmp_path):
    """Test embedding generation for short audio (< 1 second) - should pad."""
    test_audio = tmp_path / "short.wav"
    create_test_audio(test_audio, duration_sec=0.5)
    
    embedder = EmbeddingGenerator(embedding_dim=512)
    embedding = embedder.generate_embedding(test_audio)
    
    assert embedding.shape == (512,), "Should produce 512-dim embedding even for short audio"