"""FAISS indexing module for Milestone 1."""
import faiss
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)


class FAISSIndexer:
    """Manages FAISS index for similarity search (Milestone 1 - Flat L2 index)."""
    
    def __init__(self, embedding_dim: int = 512):
        """
        Initialize FAISS indexer.
        
        Args:
            embedding_dim: Dimension of embeddings (default: 512)
        """
        self.embedding_dim = embedding_dim
        self.index: Optional[faiss.Index] = None
        self.metadata: List[Dict] = []
    
    def create_index(self, index_type: str = "flat", **kwargs):
        """
        Create a new FAISS index.
        
        Args:
            index_type: Type of index ("flat", "hnsw", "ivf")
            **kwargs: Additional parameters for index creation
        """
        if index_type == "flat":
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            logger.info(f"Created FAISS Flat L2 index with dim={self.embedding_dim}")
        elif index_type == "hnsw":
            m = kwargs.get("m", 32)
            ef_construction = kwargs.get("ef_construction", 200)
            self.index = faiss.IndexHNSWFlat(self.embedding_dim, m)
            self.index.hnsw.efConstruction = ef_construction
            logger.info(f"Created HNSW index with dim={self.embedding_dim}, M={m}, efConstruction={ef_construction}")
        elif index_type == "ivf":
            nlist = kwargs.get("nlist", 100)
            quantizer = faiss.IndexFlatL2(self.embedding_dim)
            self.index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, nlist)
            logger.info(f"Created IVF index with dim={self.embedding_dim}, nlist={nlist}")
        else:
            raise ValueError(f"Unknown index type: {index_type}")
    
    def add_embeddings(
        self,
        embeddings: np.ndarray,
        metadata: List[Dict]
    ):
        """
        Add embeddings to the index.
        
        Args:
            embeddings: numpy array of shape (N, embedding_dim) - float32
            metadata: list of metadata dicts (one per embedding)
                Each dict should contain: segment_id, file_id, start, end, path, etc.
        """
        if self.index is None:
            self.create_index()
        
        # Ensure float32
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)
        
        # Ensure 2D
        if len(embeddings.shape) == 1:
            embeddings = embeddings.reshape(1, -1)
        
        # Validate dimensions
        if embeddings.shape[1] != self.embedding_dim:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.embedding_dim}, "
                f"got {embeddings.shape[1]}"
            )
        
        # Validate metadata length
        if len(metadata) != len(embeddings):
            raise ValueError(
                f"Metadata length mismatch: {len(metadata)} metadata entries "
                f"for {len(embeddings)} embeddings"
            )
        
        # Add to index
        self.index.add(embeddings)
        
        # Store metadata
        self.metadata.extend(metadata)
        
        logger.info(f"Added {len(embeddings)} embeddings. Total: {self.index.ntotal}")
    
    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Search for similar embeddings.
        
        Args:
            query_embedding: query vector (embedding_dim,) or (1, embedding_dim)
            k: number of results to return
            threshold: optional similarity threshold (0-1), filters results
        
        Returns:
            List of match dictionaries with keys:
            - segment_id: ID of matched segment
            - file_id: ID of source file
            - similarity: similarity score (0-1, higher is more similar)
            - distance: L2 distance (lower is more similar)
            - rank: rank of match (1-based)
            - All other metadata fields from original entry
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Index is empty or not created")
            return []
        
        # Prepare query
        if query_embedding.dtype != np.float32:
            query_embedding = query_embedding.astype(np.float32)
        
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Validate dimension
        if query_embedding.shape[1] != self.embedding_dim:
            raise ValueError(
                f"Query dimension mismatch: expected {self.embedding_dim}, "
                f"got {query_embedding.shape[1]}"
            )
        
        # Search
        k = min(k, self.index.ntotal)  # Don't search for more than available
        distances, indices = self.index.search(query_embedding, k)
        
        # Format results
        results = []
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
            if idx < len(self.metadata) and idx >= 0:
                # Convert L2 distance to similarity (inverse relationship)
                # L2 distance: lower is better, similarity: higher is better
                similarity = 1.0 / (1.0 + dist)
                
                # Apply threshold if provided
                if threshold is not None and similarity < threshold:
                    continue
                
                result = self.metadata[idx].copy()
                result["similarity"] = float(similarity)
                result["distance"] = float(dist)
                result["rank"] = rank
                results.append(result)
        
        return results
    
    def save_index(self, index_path: Path, metadata_path: Path):
        """
        Save index and metadata to disk.
        
        Args:
            index_path: Path to save FAISS index
            metadata_path: Path to save metadata JSON
        """
        if self.index is None:
            raise ValueError("No index to save")
        
        # Save FAISS index
        faiss.write_index(self.index, str(index_path))
        
        # Save metadata
        with open(metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=2)
        
        logger.info(f"Saved index to {index_path}, metadata to {metadata_path}")
    
    def load_index(self, index_path: Path, metadata_path: Path):
        """
        Load index and metadata from disk.
        
        Args:
            index_path: Path to FAISS index file
            metadata_path: Path to metadata JSON file
        """
        # Load FAISS index
        self.index = faiss.read_index(str(index_path))
        
        # Load metadata
        with open(metadata_path, "r") as f:
            self.metadata = json.load(f)
        
        logger.info(f"Loaded index with {self.index.ntotal} vectors from {index_path}")
    
    def get_stats(self) -> Dict:
        """
        Get index statistics.
        
        Returns:
            Dictionary with index statistics
        """
        if self.index is None:
            return {
                "total_vectors": 0,
                "embedding_dim": self.embedding_dim,
                "index_type": "None"
            }
        
        return {
            "total_vectors": self.index.ntotal,
            "embedding_dim": self.embedding_dim,
            "index_type": "IndexFlatL2"
        }