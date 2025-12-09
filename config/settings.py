"""Configuration settings for Milestone 2."""
from pathlib import Path
from typing import Dict, Optional

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
INDEXES_DIR = DATA_DIR / "indexes"
REPORTS_DIR = DATA_DIR / "reports"

# Audio processing settings
SEGMENT_LENGTH = 0.5  # seconds (default for Milestone 2)
SAMPLE_RATE = 44100
EMBEDDING_DIM = 512

# Embedding model settings (Research Paper Requirements)
EMBEDDING_MODEL_TYPE = "mert"  # "mert", "muq", "openl3", "auto" (auto tries MERT > MuQ > OpenL3)
MERT_MODEL_NAME = "m-a-p/MERT-v1-330M"  # MERT model from Hugging Face
USE_HARD_NEGATIVE_MINING = True  # Enable hard negative mining for contrastive learning
NUM_HARD_NEGATIVES = 5  # Number of hard negatives per anchor

# Stem types
STEM_TYPES = ["vocals", "drums", "bass", "other"]

# Model paths
EMBEDDING_MODEL_PATH = MODELS_DIR / "fingerprint_v1.pt"
CLASSIFIER_PATHS = {
    "vocals": MODELS_DIR / "classifier_vocals_v1.pkl",
    "drums": MODELS_DIR / "classifier_drums_v1.pkl",
    "bass": MODELS_DIR / "classifier_bass_v1.pkl",
    "other": MODELS_DIR / "classifier_other_v1.pkl"
}

# Index paths
FAISS_INDEX_PATH = INDEXES_DIR / "faiss_index.bin"
FAISS_METADATA_PATH = INDEXES_DIR / "faiss_metadata.json"

# Augmentation config
AUGMENTATION_CONFIG_PATH = BASE_DIR / "config" / "augmentation_config.yaml"

# Training settings
TRAINING_BATCH_SIZE = 32
TRAINING_EPOCHS = 10
TRAINING_LEARNING_RATE = 1e-4

# FAISS index settings
FAISS_INDEX_TYPE = "flat"  # "flat", "hnsw", "ivf"
FAISS_HNSW_M = 32
FAISS_HNSW_EF_CONSTRUCTION = 200
FAISS_IVF_NLIST = 100
FAISS_IVF_NPROBE = 10

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8000
API_WORKERS = 1

# Performance targets (from client requirements)
TARGET_PRECISION_RECALL = 0.95
TARGET_F1_SCORE = 0.90
TARGET_LATENCY_SECONDS = 1.0
TARGET_THROUGHPUT_REALTIME = 10.0
TARGET_ROBUSTNESS_DETECTION = 0.85

