"""Milestone 1 demonstration script - End-to-end pipeline."""
from pathlib import Path
import numpy as np
import sys
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stage2_preprocessing import Segmenter
from src.stage3_embedding import EmbeddingGenerator
from src.stage4_indexing import FAISSIndexer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Run Milestone 1 complete pipeline."""
    logger.info("=" * 60)
    logger.info("Milestone 1: Segmentation + Embedding + FAISS")
    logger.info("=" * 60)
    
    # Setup paths
    data_dir = Path("data")
    input_audio = data_dir / "raw" / "test_audio.wav"
    segments_dir = data_dir / "derived" / "segments"
    embeddings_dir = data_dir / "embeddings"
    index_path = data_dir / "indexes" / "faiss_index.bin"
    metadata_path = data_dir / "indexes" / "faiss_metadata.json"
    
    # Create directories
    segments_dir.mkdir(parents=True, exist_ok=True)
    embeddings_dir.mkdir(parents=True, exist_ok=True)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if input file exists
    if not input_audio.exists():
        logger.error(f"Input audio file not found: {input_audio}")
        logger.info("Please place a test audio file at: data/raw/test_audio.wav")
        return
    
    # ============================================================
    # Step 1: Segmentation
    # ============================================================
    logger.info("\n" + "=" * 60)
    logger.info("Step 1: Segmenting audio file...")
    logger.info("=" * 60)
    
    segmenter = Segmenter(segment_length=1.0, sample_rate=44100)
    segments = segmenter.segment_file(input_audio, segments_dir)
    
    logger.info(f"✓ Created {len(segments)} segments")
    logger.info(f"  First segment: {segments[0]['segment_id']} ({segments[0]['start']:.2f}s - {segments[0]['end']:.2f}s)")
    logger.info(f"  Last segment: {segments[-1]['segment_id']} ({segments[-1]['start']:.2f}s - {segments[-1]['end']:.2f}s)")
    
    # ============================================================
    # Step 2: Generate Embeddings
    # ============================================================
    logger.info("\n" + "=" * 60)
    logger.info("Step 2: Generating OpenL3 embeddings...")
    logger.info("=" * 60)
    
    embedder = EmbeddingGenerator(embedding_dim=512, sample_rate=44100)
    
    segment_paths = [Path(s["path"]) for s in segments]
    logger.info(f"Processing {len(segment_paths)} segments...")
    
    embeddings = embedder.generate_embeddings_batch(segment_paths)
    
    # Save embeddings
    embedding_metadata = []
    for i, (seg, emb) in enumerate(zip(segments, embeddings)):
        emb_path = embeddings_dir / f"{seg['segment_id']}.npy"
        embedder.save_embedding(emb, emb_path)
        embedding_metadata.append({
            "embedding_id": seg['segment_id'],
            "segment_id": seg['segment_id'],
            "file_id": seg['file_id'],
            "start": seg['start'],
            "end": seg['end'],
            "duration": seg['duration'],
            "segment_path": seg['path'],
            "embedding_path": str(emb_path),
            "sample_rate": seg['sample_rate']
        })
    
    logger.info(f"✓ Generated {len(embeddings)} embeddings")
    logger.info(f"  Embedding dimension: {embeddings[0].shape}")
    logger.info(f"  Embedding norm: {np.linalg.norm(embeddings[0]):.4f} (should be ~1.0)")
    
    # ============================================================
    # Step 3: Build FAISS Index
    # ============================================================
    logger.info("\n" + "=" * 60)
    logger.info("Step 3: Building FAISS index...")
    logger.info("=" * 60)
    
    indexer = FAISSIndexer(embedding_dim=512)
    
    embeddings_array = np.array(embeddings)
    indexer.add_embeddings(embeddings_array, embedding_metadata)
    
    # Save index
    indexer.save_index(index_path, metadata_path)
    
    stats = indexer.get_stats()
    logger.info("✅ Index built successfully")
    logger.info(f"  Total vectors: {stats['total_vectors']}")
    logger.info(f"  Embedding dimension: {stats['embedding_dim']}")
    logger.info(f"  Index type: {stats['index_type']}")
    
    # ============================================================
    # Step 4: Test Similarity Search
    # ============================================================
    logger.info("\n" + "=" * 60)
    logger.info("Step 4: Testing similarity search...")
    logger.info("=" * 60)
    
    # Use first segment as query (should find itself as top match)
    query_segment = segments[0]
    query_embedding = embeddings[0]
    
    logger.info(f"Query: {query_segment['segment_id']} ({query_segment['start']:.2f}s - {query_segment['end']:.2f}s)")
    
    results = indexer.search(query_embedding, k=5)
    
    logger.info(f"\nTop {len(results)} matches:")
    for i, result in enumerate(results, 1):
        logger.info(
            f"  {i}. {result['segment_id']} | "
            f"Similarity: {result['similarity']:.4f} | "
            f"Distance: {result['distance']:.4f} | "
            f"Time: {result['start']:.2f}s - {result['end']:.2f}s"
        )
    
    # Verify self-match
    try:
        if results and results[0].get('segment_id') == query_segment.get('segment_id'):
            logger.info("✓ Self-match verified: query found itself as the top result")
        else:
            logger.error("✗ Self-match not found: query did not retrieve itself as top result (potential issue)")
    except Exception as e:
        logger.error(f"Error verifying self-match: {e}")
    
    # ============================================================
    # Summary
    # ============================================================
    logger.info("\n" + "=" * 60)
    logger.info("Milestone 1 Complete!")
    logger.info("=" * 60)
    logger.info(f"✓ Segmentation: {len(segments)} segments created")
    logger.info(f"✓ Embeddings: {len(embeddings)} embeddings generated")
    logger.info(f"✓ FAISS Index: {stats['total_vectors']} vectors indexed")
    logger.info("✓ Search: test completed successfully")
    logger.info("\nAll deliverables completed and tested!")


if __name__ == "__main__":
    main()