# Audio Provenance System - Complete Implementation

## 🚀 Quick Start - Run & Test

**Want to deploy and test?** See these guides:

- **[QUICK_START.md](QUICK_START.md)** ⚡ - Fastest way to get started (3 steps)
- **[COMPLETE_RUN_GUIDE.md](COMPLETE_RUN_GUIDE.md)** 📖 - Complete deployment & testing guide
- **[VISUAL_TESTING_GUIDE.md](VISUAL_TESTING_GUIDE.md)** 🎨 - GUI app visual testing

**Quick Commands:**
```bash
# Deploy to VPS
cd ~/audio-ai && source venv/bin/activate && uvicorn api.main:app --host 0.0.0.0 --port 8000

# Test with GUI (on local machine)
python gui_test_app.py
```

---

A robust per-stem audio provenance system that detects AI-generated content and identifies reused samples through neural fingerprinting and similarity search.

## Features

- **Music Foundation Models**: Uses MERT (Music Encoder Representations from Transformers) - state-of-the-art music-specific embeddings
- **Stem Separation**: Separates audio into vocals, drums, bass, and other stems using Demucs
- **Neural Fingerprinting**: Generates 512-dimensional embeddings using MERT/MuQ (with OpenL3 fallback)
- **Hard Negative Mining**: Advanced contrastive learning with hard negative mining for better training
- **Similarity Search**: Large-scale similarity search using FAISS (Flat, HNSW, or IVF)
- **AI Detection**: Per-stem classifier to detect AI-generated vs human-created content
- **Robustness**: Handles compression, pitch/time shifts, EQ, reverb, and other distortions
- **Provenance Reports**: Comprehensive JSON reports with matches, probabilities, and risk flags
- **REST API**: FastAPI endpoints for programmatic access

## Installation

### Prerequisites

- Python 3.10+
- CUDA-capable GPU (recommended for Demucs and training)
- 16GB+ RAM (32GB+ recommended)
- 1TB+ storage for models and data

### Setup

```bash
# Clone repository
git clone <repo-url>
cd audio-ai

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (Git Bash):
source venv/Scripts/activate
# Windows (CMD/PowerShell):
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Test Basic Pipeline

```bash
# Create test audio (if needed)
python scripts/create_test_audio.py

# Run Milestone 1 demo (segmentation + embedding + FAISS)
python scripts/milestone1_demo.py

# Run Milestone 2 demo (complete pipeline with stems + classification)
python scripts/run_demo_m2.py
```

### 2. Train Models

```bash
# Prepare training data structure:
# data/training/
#   human/
#     *.wav (human-created audio stems)
#   ai/
#     *.wav (AI-generated audio stems)

# Train embeddings with MERT (Music Foundation Model)
# MERT will be automatically downloaded from Hugging Face on first run
python scripts/train_embeddings.py --data_dir data/training

# Train classifiers
python scripts/train_classifier.py --data_dir data/training
```

### 3. Build Index

```bash
# Generate embeddings for your audio library
python scripts/milestone1_demo.py

# Build FAISS index
python scripts/build_index.py \
  --embeddings_dir data/embeddings \
  --index_type hnsw  # or "flat" or "ivf"
```

### 4. Run API Server

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Test the API:
```bash
curl -X POST "http://localhost:8000/api/v1/provenance-check" \
  -F "file=@data/raw/test_audio.wav"
```

## Project Structure

```
audio-ai/
├── src/                    # Source code
│   ├── stage2_preprocessing/  # Segmentation & stem separation
│   ├── stage3_embedding/       # Embedding generation & training
│   ├── stage4_indexing/        # FAISS indexing
│   ├── stage5_classifier/      # AI vs Human classification
│   ├── stage6_reporting/       # Provenance report generation
│   └── pipeline/              # Pipeline orchestration
├── api/                    # FastAPI server
├── scripts/                # Training & evaluation scripts
├── config/                 # Configuration files
├── data/                   # Data directories
│   ├── raw/               # Input audio files
│   ├── derived/            # Processed segments
│   ├── embeddings/         # Generated embeddings
│   ├── indexes/            # FAISS indices
│   └── reports/            # Provenance reports
├── models/                 # Trained models
└── tests/                  # Unit tests
```

## Configuration

### Settings (`config/settings.py`)

- `SEGMENT_LENGTH`: Segment length in seconds (default: 0.5)
- `SAMPLE_RATE`: Audio sample rate (default: 44100)
- `EMBEDDING_DIM`: Embedding dimension (default: 512)
- `FAISS_INDEX_TYPE`: Index type ("flat", "hnsw", "ivf")

### Augmentation Config (`config/augmentation_config.yaml`)

Customize robustness augmentations:
- Time stretching: ±15%
- Pitch shifting: ±3 semitones
- EQ filtering, reverb, noise, etc.

## API Endpoints

### POST `/api/v1/provenance-check`

Upload audio file for provenance checking.

**Request:**
- `file`: Audio file (multipart/form-data)

**Response:**
```json
{
  "job_id": "uuid",
  "status": "processing",
  "message": "Provenance check started"
}
```

### GET `/api/v1/status/{job_id}`

Check status of provenance check job.

**Response:**
```json
{
  "status": "completed",
  "file_path": "...",
  "report_path": "..."
}
```

### GET `/api/v1/reports/{job_id}`

Get provenance report (JSON file).

## Performance Targets

- **Precision & Recall**: ≥ 95% for near-duplicate detection
- **F1 Score**: ≥ 0.90 for AI vs Human classifier
- **Latency**: < 1s for single file processing
- **Throughput**: ≥ 10× real-time
- **Robustness**: ≥ 85% detection under extreme transforms

## Evaluation

### Robustness Evaluation

```bash
python scripts/evaluate_robustness.py \
  --test_data_dir data/test \
  --index_path data/indexes/faiss_index.bin \
  --output data/reports/robustness_evaluation.json
```

### Unit Tests

```bash
pytest tests/ -v
```

## Milestones

### ✅ Milestone 1 (Completed)
- Audio segmentation (1s chunks)
- Embedding generation (OpenL3)
- FAISS indexing (Flat L2)

### ✅ Milestone 2 (Completed)
- Stem separation (Demucs)
- Robustness augmentations
- Per-stem AI classification
- Provenance reporting
- FastAPI endpoints
- Training & evaluation scripts

### 🔄 Milestone 3 (Future)
- HTML/JS frontend
- Mobile optimization
- Advanced quantization
- Real-time processing

## Troubleshooting

### Demucs Installation Issues
```bash
pip install demucs --upgrade
# If GPU issues, use CPU: export DEMUCS_DEVICE=cpu
```

### FAISS GPU Issues
```bash
# Use CPU version if GPU not available
pip uninstall faiss-gpu
pip install faiss-cpu
```

### OpenL3 Model Download
OpenL3 will download models automatically on first use. If network issues:
```bash
pip install openl3 --timeout=600 --retries=10
```

## License

See LICENSE file for details.

## Contact

For questions or issues, please contact the development team.

