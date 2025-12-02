"""Training script for embedding model with contrastive learning."""
import sys
from pathlib import Path
import numpy as np
import logging
from tqdm import tqdm
import argparse
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stage3_embedding import EmbeddingGenerator, AudioAugmentation, EmbeddingTrainer
from config.settings import (
    SEGMENT_LENGTH, SAMPLE_RATE, EMBEDDING_DIM,
    AUGMENTATION_CONFIG_PATH, MODELS_DIR, TRAINING_EPOCHS, TRAINING_BATCH_SIZE,
    EMBEDDING_MODEL_TYPE, USE_HARD_NEGATIVE_MINING, NUM_HARD_NEGATIVES
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_training_data(data_dir: Path) -> tuple:
    """
    Load training data from directory.
    
    Expected structure:
    data_dir/
        human/
            *.wav
        ai/
            *.wav
    
    Returns:
        (audio_paths, labels, stem_types)
    """
    audio_paths = []
    labels = []  # 0=human, 1=AI
    stem_types = []
    
    # Load human samples
    human_dir = data_dir / "human"
    if human_dir.exists():
        for wav_file in human_dir.glob("*.wav"):
            audio_paths.append(wav_file)
            labels.append(0)
            # Try to infer stem type from filename or directory
            stem_type = "mix"
            if "vocals" in wav_file.stem.lower():
                stem_type = "vocals"
            elif "drums" in wav_file.stem.lower():
                stem_type = "drums"
            elif "bass" in wav_file.stem.lower():
                stem_type = "bass"
            elif "other" in wav_file.stem.lower():
                stem_type = "other"
            stem_types.append(stem_type)
    
    # Load AI samples
    ai_dir = data_dir / "ai"
    if ai_dir.exists():
        for wav_file in ai_dir.glob("*.wav"):
            audio_paths.append(wav_file)
            labels.append(1)
            # Try to infer stem type
            stem_type = "mix"
            if "vocals" in wav_file.stem.lower():
                stem_type = "vocals"
            elif "drums" in wav_file.stem.lower():
                stem_type = "drums"
            elif "bass" in wav_file.stem.lower():
                stem_type = "bass"
            elif "other" in wav_file.stem.lower():
                stem_type = "other"
            stem_types.append(stem_type)
    
    logger.info(f"Loaded {len(audio_paths)} training samples")
    logger.info(f"  Human: {sum(1 for l in labels if l == 0)}")
    logger.info(f"  AI: {sum(1 for l in labels if l == 1)}")
    
    return audio_paths, np.array(labels), np.array(stem_types)


def generate_training_pairs(
    embedder: EmbeddingGenerator,
    augmenter: AudioAugmentation,
    audio_paths: list,
    labels: np.ndarray,
    num_pairs_per_sample: int = 5
) -> tuple:
    """
    Generate anchor-positive-negative triplets for contrastive learning.
    
    Returns:
        (anchors, positives, negatives)
    """
    anchors = []
    positives = []
    negatives = []
    
    logger.info("Generating training pairs...")
    
    for i, audio_path in enumerate(tqdm(audio_paths)):
        # Load audio
        import soundfile as sf
        audio, sr = sf.read(audio_path)
        
        # Ensure correct length
        target_samples = int(SAMPLE_RATE * SEGMENT_LENGTH)
        if len(audio) < target_samples:
            audio = np.pad(audio, (0, target_samples - len(audio)))
        elif len(audio) > target_samples:
            audio = audio[:target_samples]
        
        # Generate anchor embedding
        anchor_emb = embedder.generate_embedding(audio_path)
        
        # Generate positive (augmented version)
        aug_audios = augmenter.augment(audio, sr, num_augmentations=1)
        if aug_audios:
            # Save augmented audio temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                sf.write(tmp.name, aug_audios[0], sr)
                positive_emb = embedder.generate_embedding(Path(tmp.name))
                Path(tmp.name).unlink()
        else:
            positive_emb = anchor_emb.copy()
        
        # Find negative (different label)
        negative_indices = np.where(labels != labels[i])[0]
        if len(negative_indices) > 0:
            neg_idx = np.random.choice(negative_indices)
            negative_emb = embedder.generate_embedding(audio_paths[neg_idx])
        else:
            # Use random embedding if no negative available
            negative_emb = np.random.randn(EMBEDDING_DIM).astype(np.float32)
            negative_emb = negative_emb / np.linalg.norm(negative_emb)
        
        anchors.append(anchor_emb)
        positives.append(positive_emb)
        negatives.append(negative_emb)
    
    return np.array(anchors), np.array(positives), np.array(negatives)


def main():
    parser = argparse.ArgumentParser(description="Train embedding model with contrastive learning")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to training data directory")
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory for model")
    parser.add_argument("--epochs", type=int, default=TRAINING_EPOCHS, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=TRAINING_BATCH_SIZE, help="Batch size")
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return
    
    output_dir = Path(args.output_dir) if args.output_dir else MODELS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize components
    embedder = EmbeddingGenerator(
        embedding_dim=EMBEDDING_DIM,
        sample_rate=SAMPLE_RATE,
        model_type=EMBEDDING_MODEL_TYPE
    )
    augmenter = AudioAugmentation(config_path=AUGMENTATION_CONFIG_PATH)
    trainer = EmbeddingTrainer(
        embedding_dim=EMBEDDING_DIM,
        use_hard_negatives=USE_HARD_NEGATIVE_MINING,
        num_hard_negatives=NUM_HARD_NEGATIVES
    )
    
    # Log model info
    model_info = embedder.get_model_info()
    logger.info(f"Using embedding model: {model_info['active_model']}")
    logger.info(f"Model info: {model_info}")
    
    # Load training data
    audio_paths, labels, stem_types = load_training_data(data_dir)
    
    if len(audio_paths) == 0:
        logger.error("No training data found!")
        return
    
    # Generate training pairs
    anchors, positives, negatives = generate_training_pairs(
        embedder, augmenter, audio_paths, labels
    )
    
    # Create candidate pool for hard negative mining
    candidate_pool = None
    if USE_HARD_NEGATIVE_MINING:
        # Use all embeddings as candidate pool for hard negative mining
        logger.info("Building candidate pool for hard negative mining...")
        candidate_pool = np.vstack([anchors, positives, negatives.reshape(-1, EMBEDDING_DIM)])
        logger.info(f"Candidate pool size: {len(candidate_pool)}")
    
    # Train
    logger.info("Starting training...")
    for epoch in range(args.epochs):
        loss = trainer.train_epoch(
            anchors, positives, negatives,
            candidate_pool=candidate_pool,
            batch_size=args.batch_size
        )
        logger.info(f"Epoch {epoch+1}/{args.epochs}, Loss: {loss:.4f}")
    
    # Save model
    model_path = output_dir / "fingerprint_v1.pt"
    trainer.save_model(model_path)
    
    # Save training metadata
    metadata = {
        "embedding_dim": EMBEDDING_DIM,
        "sample_rate": SAMPLE_RATE,
        "segment_length": SEGMENT_LENGTH,
        "num_samples": len(audio_paths),
        "epochs": args.epochs,
        "final_loss": float(loss)
    }
    
    metadata_path = output_dir / "fingerprint_v1_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Training complete! Model saved to {model_path}")


if __name__ == "__main__":
    main()

