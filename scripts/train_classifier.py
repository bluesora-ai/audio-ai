"""Training script for per-stem AI vs Human classifier."""
import sys
from pathlib import Path
import numpy as np
import logging
import argparse
import json
from sklearn.model_selection import train_test_split

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stage3_embedding import EmbeddingGenerator
from src.stage5_classifier import AIDetector
from config.settings import (
    SEGMENT_LENGTH, SAMPLE_RATE, EMBEDDING_DIM,
    MODELS_DIR, CLASSIFIER_PATHS, STEM_TYPES
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_training_data(data_dir: Path) -> tuple:
    """
    Load training data with embeddings.
    
    Expected structure:
    data_dir/
        human/
            *.wav
        ai/
            *.wav
    
    Returns:
        (embeddings, labels, stem_types)
    """
    embedder = EmbeddingGenerator(embedding_dim=EMBEDDING_DIM, sample_rate=SAMPLE_RATE)
    
    embeddings = []
    labels = []  # 0=human, 1=AI
    stem_types = []
    
    # Load human samples
    human_dir = data_dir / "human"
    if human_dir.exists():
        for wav_file in human_dir.glob("*.wav"):
            try:
                emb = embedder.generate_embedding(wav_file)
                embeddings.append(emb)
                labels.append(0)
                
                # Infer stem type from filename
                stem_type = "mix"
                filename_lower = wav_file.stem.lower()
                for st in STEM_TYPES:
                    if st in filename_lower:
                        stem_type = st
                        break
                stem_types.append(stem_type)
            except Exception as e:
                logger.warning(f"Failed to process {wav_file}: {e}")
    
    # Load AI samples
    ai_dir = data_dir / "ai"
    if ai_dir.exists():
        for wav_file in ai_dir.glob("*.wav"):
            try:
                emb = embedder.generate_embedding(wav_file)
                embeddings.append(emb)
                labels.append(1)
                
                # Infer stem type
                stem_type = "mix"
                filename_lower = wav_file.stem.lower()
                for st in STEM_TYPES:
                    if st in filename_lower:
                        stem_type = st
                        break
                stem_types.append(stem_type)
            except Exception as e:
                logger.warning(f"Failed to process {wav_file}: {e}")
    
    embeddings = np.array(embeddings)
    labels = np.array(labels)
    stem_types = np.array(stem_types)
    
    logger.info(f"Loaded {len(embeddings)} training samples")
    logger.info(f"  Human: {sum(labels == 0)}")
    logger.info(f"  AI: {sum(labels == 1)}")
    
    return embeddings, labels, stem_types


def train_classifiers(
    embeddings: np.ndarray,
    labels: np.ndarray,
    stem_types: np.ndarray,
    output_dir: Path,
    test_size: float = 0.2
):
    """
    Train classifiers for each stem type.
    
    Args:
        embeddings: All embeddings (N, dim)
        labels: All labels (N,)
        stem_types: All stem types (N,)
        output_dir: Output directory
        test_size: Test set size ratio
    """
    results = {}
    
    # Train per-stem classifiers
    for stem_type in STEM_TYPES:
        logger.info(f"\nTraining classifier for {stem_type}...")
        
        # Filter by stem type
        mask = stem_types == stem_type
        stem_embeddings = embeddings[mask]
        stem_labels = labels[mask]
        
        if len(stem_embeddings) == 0:
            logger.warning(f"No samples for {stem_type}, skipping...")
            continue
        
        logger.info(f"  Samples: {len(stem_embeddings)} (Human: {sum(stem_labels == 0)}, AI: {sum(stem_labels == 1)})")
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            stem_embeddings, stem_labels, test_size=test_size, random_state=42, stratify=stem_labels
        )
        
        # Train classifier
        detector = AIDetector(stem_type=stem_type)
        detector.train(X_train, y_train, calibration=True)
        
        # Evaluate
        metrics = detector.evaluate(X_test, y_test)
        logger.info(f"  Test metrics: {metrics}")
        
        # Save model
        model_path = output_dir / f"classifier_{stem_type}_v1.pkl"
        detector.save_model(model_path)
        
        results[stem_type] = {
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "metrics": metrics,
            "model_path": str(model_path)
        }
    
    # Also train a general classifier (all stems combined)
    logger.info("\nTraining general classifier (all stems)...")
    X_train, X_test, y_train, y_test = train_test_split(
        embeddings, labels, test_size=test_size, random_state=42, stratify=labels
    )
    
    # Get train indices for stem_types
    train_indices, _ = train_test_split(
        np.arange(len(embeddings)), test_size=test_size, random_state=42, stratify=labels
    )
    
    detector = AIDetector(stem_type=None)
    detector.train(X_train, y_train, stem_types=stem_types[train_indices], calibration=True)
    
    metrics = detector.evaluate(X_test, y_test)
    logger.info(f"  Test metrics: {metrics}")
    
    model_path = output_dir / "classifier_general_v1.pkl"
    detector.save_model(model_path)
    
    results["general"] = {
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "metrics": metrics,
        "model_path": str(model_path)
    }
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Train AI vs Human classifier")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to training data directory")
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory for models")
    parser.add_argument("--test_size", type=float, default=0.2, help="Test set size ratio")
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return
    
    output_dir = Path(args.output_dir) if args.output_dir else MODELS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load training data
    embeddings, labels, stem_types = load_training_data(data_dir)
    
    if len(embeddings) == 0:
        logger.error("No training data found!")
        return
    
    # Train classifiers
    results = train_classifiers(embeddings, labels, stem_types, output_dir, args.test_size)
    
    # Save results
    results_path = output_dir / "classifier_training_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\nTraining complete! Results saved to {results_path}")


if __name__ == "__main__":
    main()

