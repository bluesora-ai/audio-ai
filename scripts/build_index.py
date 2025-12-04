"""Script to build FAISS index from embeddings."""
import sys
from pathlib import Path
import numpy as np
import logging
import argparse
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stage4_indexing import FAISSIndexer
from config.settings import (
    EMBEDDING_DIM, INDEXES_DIR, FAISS_INDEX_PATH, FAISS_METADATA_PATH,
    FAISS_INDEX_TYPE, FAISS_HNSW_M, FAISS_HNSW_EF_CONSTRUCTION
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_embeddings_from_directory(embeddings_dir: Path) -> tuple:
    """
    Load embeddings and metadata from directory.
    
    Expected structure:
    embeddings_dir/
        *.npy files
    
    Returns:
        (embeddings_array, metadata_list)
    """
    embeddings = []
    metadata = []
    
    for npy_file in sorted(embeddings_dir.glob("*.npy")):
        try:
            emb = np.load(npy_file)
            embeddings.append(emb)
            
            # Try to load corresponding metadata
            metadata_file = npy_file.with_suffix('.json')
            if metadata_file.exists():
                import json
                with open(metadata_file, 'r') as f:
                    meta = json.load(f)
            else:
                # Create basic metadata from filename
                meta = {
                    "segment_id": npy_file.stem,
                    "file_id": npy_file.stem.split('_')[0] if '_' in npy_file.stem else npy_file.stem,
                    "embedding_path": str(npy_file)
                }
            
            metadata.append(meta)
        except Exception as e:
            logger.warning(f"Failed to load {npy_file}: {e}")
    
    if len(embeddings) == 0:
        raise ValueError(f"No embeddings found in {embeddings_dir}")
    
    embeddings_array = np.array(embeddings)
    logger.info(f"Loaded {len(embeddings)} embeddings with shape {embeddings_array.shape}")
    
    return embeddings_array, metadata


def create_index(
    indexer: FAISSIndexer,
    index_type: str,
    num_vectors: int,
    nlist: int = 4096,
    pq_m: int = 64,
    nbits: int = 8
):
    """Create FAISS index of specified type."""
    if index_type == "flat":
        indexer.create_index("flat")
    elif index_type == "hnsw":
        indexer.create_index("hnsw", m=FAISS_HNSW_M, ef_construction=FAISS_HNSW_EF_CONSTRUCTION)
    elif index_type == "ivf":
        indexer.create_index("ivf", nlist=nlist)
    elif index_type == "ivfpq":
        indexer.create_index("ivfpq", nlist=nlist, pq_m=pq_m, nbits=nbits)
        logger.info(f"Created IVF+PQ index with nlist={nlist}, PQ_m={pq_m}, nbits={nbits}")
    else:
        raise ValueError(f"Unknown index type: {index_type}")


def main():
    parser = argparse.ArgumentParser(description="Build FAISS index from embeddings")
    parser.add_argument("--embeddings_dir", type=str, required=True, help="Directory containing .npy embedding files")
    parser.add_argument("--index_path", type=str, default=None, help="Output path for index")
    parser.add_argument("--metadata_path", type=str, default=None, help="Output path for metadata")
    parser.add_argument("--index_type", type=str, default=FAISS_INDEX_TYPE, choices=["flat", "hnsw", "ivf", "ivfpq"], help="Index type")
    parser.add_argument("--nlist", type=int, default=4096, help="Number of clusters for IVF/IVF+PQ (default: 4096)")
    parser.add_argument("--pq_m", type=int, default=64, help="Number of subquantizers for IVF+PQ (default: 64)")
    parser.add_argument("--nbits", type=int, default=8, help="Bits per subquantizer for IVF+PQ (default: 8)")
    parser.add_argument("--nprobe", type=int, default=8, help="Number of clusters to probe for IVF/IVF+PQ (default: 8)")
    
    args = parser.parse_args()
    
    embeddings_dir = Path(args.embeddings_dir)
    if not embeddings_dir.exists():
        logger.error(f"Embeddings directory not found: {embeddings_dir}")
        return
    
    index_path = Path(args.index_path) if args.index_path else FAISS_INDEX_PATH
    metadata_path = Path(args.metadata_path) if args.metadata_path else FAISS_METADATA_PATH
    
    index_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load embeddings
    logger.info("Loading embeddings...")
    embeddings, metadata = load_embeddings_from_directory(embeddings_dir)
    
    # Create indexer
    indexer = FAISSIndexer(embedding_dim=EMBEDDING_DIM)
    
    # Create index
    logger.info(f"Creating {args.index_type} index...")
    create_index(
        indexer,
        args.index_type,
        len(embeddings),
        nlist=args.nlist,
        pq_m=args.pq_m,
        nbits=args.nbits
    )
    
    # Add embeddings
    logger.info("Adding embeddings to index...")
    indexer.add_embeddings(embeddings, metadata)
    
    # Set nprobe for IVF indices
    if args.index_type in ["ivf", "ivfpq"] and hasattr(indexer.index, 'nprobe'):
        indexer.index.nprobe = args.nprobe
        logger.info(f"Set nprobe={args.nprobe} for {args.index_type} index")
    
    # Save index with config
    logger.info(f"Saving index to {index_path}...")
    config_path = index_path.parent / "index_config.json"
    indexer.save_index(index_path, metadata_path, config_path)
    
    logger.info(f"Index built successfully!")
    logger.info(f"  Type: {args.index_type}")
    logger.info(f"  Vectors: {len(embeddings)}")
    logger.info(f"  Index saved to: {index_path}")
    logger.info(f"  Metadata saved to: {metadata_path}")


if __name__ == "__main__":
    main()

