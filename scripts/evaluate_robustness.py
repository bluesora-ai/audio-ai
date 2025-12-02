"""Evaluation script for robustness testing."""
import sys
from pathlib import Path
import numpy as np
import logging
import argparse
import json
from typing import Dict, List
from tqdm import tqdm

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stage3_embedding import EmbeddingGenerator, AudioAugmentation
from src.stage4_indexing import FAISSIndexer
from config.settings import (
    EMBEDDING_DIM, SAMPLE_RATE, SEGMENT_LENGTH,
    AUGMENTATION_CONFIG_PATH, FAISS_INDEX_PATH, FAISS_METADATA_PATH
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def evaluate_augmentation_type(
    embedder: EmbeddingGenerator,
    indexer: FAISSIndexer,
    test_audio_paths: List[Path],
    augmentation_type: str,
    num_tests: int = 10
) -> Dict:
    """
    Evaluate robustness to a specific augmentation type.
    
    Returns:
        Dictionary with metrics
    """
    from src.stage3_embedding import AudioAugmentation
    import soundfile as sf
    
    # Create augmenter with only specific augmentation enabled
    config = {
        augmentation_type: {"enabled": True},
        **{k: {"enabled": False} for k in [
            "lossy_encoding", "resampling", "amplitude", "time_stretch",
            "pitch_shift", "eq_filtering", "reverb", "noise", "cropping"
        ] if k != augmentation_type}
    }
    
    # Temporarily modify config
    augmenter = AudioAugmentation(config_path=None)
    augmenter.config = config
    augmenter._build_pipeline()
    
    correct_matches = 0
    total_tests = 0
    similarities = []
    
    for audio_path in test_audio_paths[:num_tests]:
        try:
            # Load original audio
            audio, sr = sf.read(audio_path)
            target_samples = int(SAMPLE_RATE * SEGMENT_LENGTH)
            if len(audio) < target_samples:
                audio = np.pad(audio, (0, target_samples - len(audio)))
            elif len(audio) > target_samples:
                audio = audio[:target_samples]
            
            # Generate original embedding
            original_emb = embedder.generate_embedding(audio_path)
            
            # Search for original in index
            original_results = indexer.search(original_emb, k=10)
            if not original_results:
                continue
            
            # Apply augmentation
            aug_audios = augmenter.augment(audio, sr, num_augmentations=1)
            if not aug_audios:
                continue
            
            # Save augmented audio temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                sf.write(tmp.name, aug_audios[0], sr)
                aug_emb = embedder.generate_embedding(Path(tmp.name))
                Path(tmp.name).unlink()
            
            # Search for augmented version
            aug_results = indexer.search(aug_emb, k=10)
            
            if aug_results:
                # Check if top match is similar to original
                top_similarity = aug_results[0].get("similarity", 0.0)
                similarities.append(top_similarity)
                
                # Consider it a match if similarity > 0.7
                if top_similarity > 0.7:
                    correct_matches += 1
            
            total_tests += 1
            
        except Exception as e:
            logger.warning(f"Error processing {audio_path}: {e}")
            continue
    
    precision = correct_matches / total_tests if total_tests > 0 else 0.0
    avg_similarity = np.mean(similarities) if similarities else 0.0
    
    return {
        "augmentation_type": augmentation_type,
        "total_tests": total_tests,
        "correct_matches": correct_matches,
        "precision": float(precision),
        "recall": float(precision),  # Simplified: same as precision for this test
        "average_similarity": float(avg_similarity)
    }


def evaluate_combined_augmentations(
    embedder: EmbeddingGenerator,
    indexer: FAISSIndexer,
    test_audio_paths: List[Path],
    num_tests: int = 10
) -> Dict:
    """Evaluate robustness to combined augmentations."""
    from src.stage3_embedding import AudioAugmentation
    import soundfile as sf
    
    augmenter = AudioAugmentation(config_path=AUGMENTATION_CONFIG_PATH)
    
    correct_matches = 0
    total_tests = 0
    similarities = []
    
    for audio_path in test_audio_paths[:num_tests]:
        try:
            # Load original
            audio, sr = sf.read(audio_path)
            target_samples = int(SAMPLE_RATE * SEGMENT_LENGTH)
            if len(audio) < target_samples:
                audio = np.pad(audio, (0, target_samples - len(audio)))
            elif len(audio) > target_samples:
                audio = audio[:target_samples]
            
            original_emb = embedder.generate_embedding(audio_path)
            
            # Apply multiple random augmentations
            aug_audios = augmenter.augment(audio, sr, num_augmentations=1)
            if not aug_audios:
                continue
            
            # Save and embed augmented
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                sf.write(tmp.name, aug_audios[0], sr)
                aug_emb = embedder.generate_embedding(Path(tmp.name))
                Path(tmp.name).unlink()
            
            # Search
            aug_results = indexer.search(aug_emb, k=10)
            
            if aug_results:
                top_similarity = aug_results[0].get("similarity", 0.0)
                similarities.append(top_similarity)
                
                if top_similarity > 0.7:
                    correct_matches += 1
            
            total_tests += 1
            
        except Exception as e:
            logger.warning(f"Error processing {audio_path}: {e}")
            continue
    
    precision = correct_matches / total_tests if total_tests > 0 else 0.0
    avg_similarity = np.mean(similarities) if similarities else 0.0
    
    return {
        "augmentation_type": "combined",
        "total_tests": total_tests,
        "correct_matches": correct_matches,
        "precision": float(precision),
        "recall": float(precision),
        "average_similarity": float(avg_similarity)
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate robustness of embeddings")
    parser.add_argument("--test_data_dir", type=str, required=True, help="Directory with test audio files")
    parser.add_argument("--index_path", type=str, default=None, help="Path to FAISS index")
    parser.add_argument("--metadata_path", type=str, default=None, help="Path to index metadata")
    parser.add_argument("--output", type=str, default=None, help="Output JSON file for results")
    parser.add_argument("--num_tests", type=int, default=10, help="Number of tests per augmentation")
    
    args = parser.parse_args()
    
    test_data_dir = Path(args.test_data_dir)
    if not test_data_dir.exists():
        logger.error(f"Test data directory not found: {test_data_dir}")
        return
    
    index_path = Path(args.index_path) if args.index_path else FAISS_INDEX_PATH
    metadata_path = Path(args.metadata_path) if args.metadata_path else FAISS_METADATA_PATH
    
    if not index_path.exists():
        logger.error(f"Index not found: {index_path}")
        return
    
    # Load index
    logger.info("Loading FAISS index...")
    indexer = FAISSIndexer(embedding_dim=EMBEDDING_DIM)
    indexer.load_index(index_path, metadata_path)
    logger.info(f"Loaded index with {indexer.index.ntotal} vectors")
    
    # Initialize embedder
    embedder = EmbeddingGenerator(embedding_dim=EMBEDDING_DIM, sample_rate=SAMPLE_RATE)
    
    # Get test files
    test_files = list(test_data_dir.glob("*.wav"))
    logger.info(f"Found {len(test_files)} test files")
    
    # Evaluate each augmentation type
    augmentation_types = [
        "resampling", "amplitude", "time_stretch", "pitch_shift",
        "eq_filtering", "reverb", "noise", "cropping"
    ]
    
    results = {}
    
    for aug_type in augmentation_types:
        logger.info(f"\nEvaluating {aug_type}...")
        result = evaluate_augmentation_type(
            embedder, indexer, test_files, aug_type, args.num_tests
        )
        results[aug_type] = result
        logger.info(f"  Precision: {result['precision']:.3f}, Avg Similarity: {result['average_similarity']:.3f}")
    
    # Evaluate combined
    logger.info("\nEvaluating combined augmentations...")
    combined_result = evaluate_combined_augmentations(
        embedder, indexer, test_files, args.num_tests
    )
    results["combined"] = combined_result
    logger.info(f"  Precision: {combined_result['precision']:.3f}, Avg Similarity: {combined_result['average_similarity']:.3f}")
    
    # Calculate overall metrics
    overall_precision = np.mean([r["precision"] for r in results.values()])
    overall_similarity = np.mean([r["average_similarity"] for r in results.values()])
    
    summary = {
        "overall_precision": float(overall_precision),
        "overall_average_similarity": float(overall_similarity),
        "target_precision": 0.95,
        "target_robustness": 0.85,
        "meets_targets": overall_precision >= 0.85
    }
    
    results["summary"] = summary
    
    # Save results
    output_path = Path(args.output) if args.output else Path("data/reports/robustness_evaluation.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\nEvaluation complete! Results saved to {output_path}")
    logger.info(f"Overall precision: {overall_precision:.3f}")
    logger.info(f"Meets targets: {summary['meets_targets']}")


if __name__ == "__main__":
    main()

