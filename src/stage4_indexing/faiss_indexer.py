"""FAISS indexing module for Milestone 1."""
import faiss
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
import json
import logging
from datetime import datetime

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
        elif index_type == "ivfpq":
            # IVF + Product Quantization for production scale
            nlist = kwargs.get("nlist", 4096)
            pq_m = kwargs.get("pq_m", 64)  # Number of subquantizers
            nbits = kwargs.get("nbits", 8)  # Bits per subquantizer
            quantizer = faiss.IndexFlatL2(self.embedding_dim)
            self.index = faiss.IndexIVFPQ(quantizer, self.embedding_dim, nlist, pq_m, nbits)
            logger.info(f"Created IVF+PQ index with dim={self.embedding_dim}, nlist={nlist}, PQ_m={pq_m}, nbits={nbits}")
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
        
        # For IVF and IVF+PQ indices, need to train quantizer first
        if hasattr(self.index, 'is_trained') and not self.index.is_trained:
            logger.info("Training quantizer for IVF/IVF+PQ index...")
            # Need at least nlist samples to train
            min_train_samples = min(len(embeddings), self.index.nlist * 39)  # FAISS requirement
            if len(embeddings) >= min_train_samples:
                self.index.train(embeddings[:min_train_samples])
            else:
                logger.warning(f"Not enough samples to train quantizer. Need at least {min_train_samples}, got {len(embeddings)}")
        
        # Add to index
        self.index.add(embeddings)
        
        # Store metadata
        self.metadata.extend(metadata)
        
        logger.info(f"Added {len(embeddings)} embeddings. Total: {self.index.ntotal}")
    
    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        threshold: Optional[float] = None,
        nprobe: Optional[int] = None
    ) -> List[Dict]:
        """
        Search for similar embeddings.
        
        Args:
            query_embedding: query vector (embedding_dim,) or (1, embedding_dim)
            k: number of results to return
            threshold: optional similarity threshold (0-1), filters results
            nprobe: number of clusters to probe (for IVF/IVF+PQ indices)
        
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
        
        # Set nprobe for IVF indices
        if hasattr(self.index, 'nprobe') and nprobe is not None:
            self.index.nprobe = nprobe
        elif hasattr(self.index, 'nprobe') and self.index.nprobe == 1:
            # Set default nprobe if not set
            self.index.nprobe = min(8, self.index.nlist // 4) if hasattr(self.index, 'nlist') else 8
        
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
    
    def save_index(
        self,
        index_path: Path,
        metadata_path: Path,
        config_path: Optional[Path] = None
    ):
        """
        Save index, metadata, and config to disk.
        
        Args:
            index_path: Path to save FAISS index
            metadata_path: Path to save metadata JSON
            config_path: Path to save index config JSON (optional)
        """
        if self.index is None:
            raise ValueError("No index to save")
        
        # Save FAISS index
        faiss.write_index(self.index, str(index_path))
        
        # Save metadata
        with open(metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=2)
        
        # Save index config
        if config_path:
            config = {
                "embedding_dim": self.embedding_dim,
                "total_vectors": self.index.ntotal,
                "index_type": str(type(self.index).__name__),
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Add index-specific parameters
            if hasattr(self.index, 'nlist'):
                config["nlist"] = self.index.nlist
            if hasattr(self.index, 'nprobe'):
                config["nprobe"] = self.index.nprobe
            if hasattr(self.index, 'pq'):
                config["pq_m"] = self.index.pq.M
                config["pq_nbits"] = self.index.pq.nbits
            
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved index config to {config_path}")
        
        logger.info(f"Saved index to {index_path}, metadata to {metadata_path}")
    
    def load_index(self, index_path: Path, metadata_path: Path):
        """
        Load index and metadata from disk.
        
        Args:
            index_path: Path to FAISS index file
            metadata_path: Path to metadata JSON file
        """
        try:
            # Load FAISS index
            logger.info(f"Attempting to load FAISS index from: {index_path}")
            if not index_path.exists():
                raise FileNotFoundError(f"Index file not found: {index_path}")
            if not metadata_path.exists():
                raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
            
            self.index = faiss.read_index(str(index_path))
            
            # Load metadata
            with open(metadata_path, "r") as f:
                self.metadata = json.load(f)
            
            logger.info(f"✅ Successfully loaded index with {self.index.ntotal} vectors from {index_path}")
            logger.info(f"   Metadata entries: {len(self.metadata)}")
            logger.info(f"   Index type: {type(self.index).__name__}")
            
            # Verify consistency
            if self.index.ntotal != len(self.metadata):
                logger.warning(f"⚠️ Index has {self.index.ntotal} vectors but metadata has {len(self.metadata)} entries")
        except Exception as e:
            logger.error(f"❌ Failed to load index: {e}")
            logger.error(f"   Index path: {index_path}")
            logger.error(f"   Metadata path: {metadata_path}")
            raise  # Re-raise to let caller know it failed
    
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
        
        index_type_name = str(type(self.index).__name__)
        
        stats = {
            "total_vectors": self.index.ntotal,
            "embedding_dim": self.embedding_dim,
            "index_type": index_type_name
        }
        
        # Add index-specific stats
        if hasattr(self.index, 'nlist'):
            stats["nlist"] = self.index.nlist
        if hasattr(self.index, 'nprobe'):
            stats["nprobe"] = self.index.nprobe
        if hasattr(self.index, 'pq'):
            stats["pq_m"] = self.index.pq.M
            stats["pq_nbits"] = self.index.pq.nbits
        
        return stats