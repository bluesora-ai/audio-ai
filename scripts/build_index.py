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
    num_vectors: int
):
    """Create FAISS index of specified type."""
    import faiss
    
    if index_type == "flat":
        indexer.create_index()
    elif index_type == "hnsw":
        # HNSW index for approximate search
        index = faiss.IndexHNSWFlat(EMBEDDING_DIM, FAISS_HNSW_M)
        index.hnsw.efConstruction = FAISS_HNSW_EF_CONSTRUCTION
        indexer.index = index
        logger.info(f"Created HNSW index with M={FAISS_HNSW_M}, efConstruction={FAISS_HNSW_EF_CONSTRUCTION}")
    elif index_type == "ivf":
        # IVF index for large-scale search
        nlist = min(100, num_vectors // 10)  # Number of clusters
        quantizer = faiss.IndexFlatL2(EMBEDDING_DIM)
        index = faiss.IndexIVFFlat(quantizer, EMBEDDING_DIM, nlist)
        indexer.index = index
        logger.info(f"Created IVF index with nlist={nlist}")
    else:
        raise ValueError(f"Unknown index type: {index_type}")


def main():
    parser = argparse.ArgumentParser(description="Build FAISS index from embeddings")
    parser.add_argument("--embeddings_dir", type=str, required=True, help="Directory containing .npy embedding files")
    parser.add_argument("--index_path", type=str, default=None, help="Output path for index")
    parser.add_argument("--metadata_path", type=str, default=None, help="Output path for metadata")
    parser.add_argument("--index_type", type=str, default=FAISS_INDEX_TYPE, choices=["flat", "hnsw", "ivf"], help="Index type")
    
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
    create_index(indexer, args.index_type, len(embeddings))
    
    # Add embeddings
    logger.info("Adding embeddings to index...")
    indexer.add_embeddings(embeddings, metadata)
    
    # Save index
    logger.info(f"Saving index to {index_path}...")
    indexer.save_index(index_path, metadata_path)
    
    # Save index config
    config = {
        "index_type": args.index_type,
        "embedding_dim": EMBEDDING_DIM,
        "num_vectors": len(embeddings),
        "index_path": str(index_path),
        "metadata_path": str(metadata_path)
    }
    
    config_path = index_path.parent / "index_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Index built successfully!")
    logger.info(f"  Type: {args.index_type}")
    logger.info(f"  Vectors: {len(embeddings)}")
    logger.info(f"  Index saved to: {index_path}")
    logger.info(f"  Metadata saved to: {metadata_path}")


if __name__ == "__main__":
    main()

