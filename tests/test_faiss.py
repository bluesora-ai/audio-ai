"""Tests for FAISS indexing module."""
import pytest
from pathlib import Path
import numpy as np
from src.stage4_indexing import FAISSIndexer


def test_faiss_index_creation():
    """Test FAISS index creation."""
    indexer = FAISSIndexer(embedding_dim=512)
    indexer.create_index()
    
    stats = indexer.get_stats()
    assert stats["total_vectors"] == 0, "New index should be empty"
    assert stats["embedding_dim"] == 512, "Index should have correct dimension"


def test_faiss_add_embeddings():
    """Test adding embeddings to index."""
    indexer = FAISSIndexer(embedding_dim=512)
    
    # Create dummy embeddings
    num_embeddings = 10
    embeddings = np.random.randn(num_embeddings, 512).astype(np.float32)
    # Normalize (numpy uses keepdims, not keepdim)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms
    
    metadata = [
        {
            "segment_id": f"seg_{i:04d}",
            "file_id": "test_file",
            "start": float(i),
            "end": float(i + 1),
            "path": f"seg_{i:04d}.wav"
        }
        for i in range(num_embeddings)
    ]
    
    indexer.add_embeddings(embeddings, metadata)
    
    stats = indexer.get_stats()
    assert stats["total_vectors"] == num_embeddings, "Index should contain all embeddings"


def test_faiss_search():
    """Test similarity search."""
    indexer = FAISSIndexer(embedding_dim=512)
    
    # Create and add embeddings
    num_embeddings = 10
    embeddings = np.random.randn(num_embeddings, 512).astype(np.float32)
    # Normalize
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms
    
    metadata = [
        {
            "segment_id": f"seg_{i:04d}",
            "file_id": "test_file",
            "start": float(i),
            "end": float(i + 1)
        }
        for i in range(num_embeddings)
    ]
    
    indexer.add_embeddings(embeddings, metadata)
    
    # Search with first embedding as query (should find itself)
    query = embeddings[0]
    results = indexer.search(query, k=5)
    
    assert len(results) > 0, "Search should return results"
    assert results[0]["segment_id"] == "seg_0000", "Top result should be the query itself"
    assert results[0]["similarity"] > 0.9, "Self-similarity should be high"


def test_faiss_save_load(tmp_path):
    """Test saving and loading index."""
    indexer = FAISSIndexer(embedding_dim=512)
    
    # Create and add embeddings
    embeddings = np.random.randn(5, 512).astype(np.float32)
    # Normalize
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms
    
    metadata = [{"segment_id": f"seg_{i:04d}"} for i in range(5)]
    indexer.add_embeddings(embeddings, metadata)
    
    # Save
    index_path = tmp_path / "test_index.bin"
    metadata_path = tmp_path / "test_metadata.json"
    indexer.save_index(index_path, metadata_path)
    
    # Load
    new_indexer = FAISSIndexer(embedding_dim=512)
    new_indexer.load_index(index_path, metadata_path)
    
    assert new_indexer.get_stats()["total_vectors"] == 5, "Loaded index should have 5 vectors"
    
    # Test search still works
    results = new_indexer.search(embeddings[0], k=3)
    assert len(results) == 3, "Search should work after loading"