# Audio AI Fingerprinting System

A production-grade audio fingerprinting and provenance detection system using OpenL3 embeddings and FAISS indexing to identify AI-generated audio content.

> **📹 [Watch Milestone 1 Demo Video](./milestone1.mp4)** - Complete end-to-end pipeline walkthrough

---

## Table of Contents

- [Quick Start](#quick-start)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Architecture](#architecture)
- [Milestone 1: Implementation & Results](#milestone-1-implementation--results)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run complete pipeline
python scripts/milestone1_demo.py

# Run tests
pytest tests/ -v
```

**Expected Results**: 92 segments created → 92 embeddings generated → FAISS index built → Similarity search validated


---

## Installation

### Step 1: System Dependencies (Windows Only)

```powershell
# Install Visual C++ Redistributables (required for TensorFlow)
winget install Microsoft.VCRedist.2015+.x64
# OR download: https://aka.ms/vs/17/release/vc_redist.x64.exe

# Restart terminal/IDE after installation
```

### Step 2: Python Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Verify Installation

```bash
python -c "import openl3, tensorflow, faiss; print('✓ All dependencies installed')"
```

**Installation Time**: 5-10 minutes

---

## Architecture

### Pipeline Stages

```
Stage 1: Ingestion      → File validation & manifest management
Stage 2: Preprocessing  → Audio segmentation (1-second segments)
Stage 3: Embedding      → OpenL3 embedding generation (512-dim)
Stage 4: Indexing       → FAISS similarity search index
Stage 5: Classifier     → AI detection (planned)
Stage 6: Reporting      → Provenance API (planned)
```

### Module Structure

```
src/
├── stage2_preprocessing/  # Segmentation
├── stage3_embedding/      # OpenL3 embeddings
└── stage4_indexing/       # FAISS index
```

---

## Milestone 1: Implementation & Results

### Implementation Highlights

**Segmentation** (`src/stage2_preprocessing/segmenter.py`)
- Fixed 1-second segments at 44.1kHz
- Automatic stereo-to-mono conversion
- Zero-padding for short files

**Embedding Generation** (`src/stage3_embedding/embedding_generator.py`)
- OpenL3 model (512-dimensional embeddings)
- Model pre-loading optimization (eliminates TensorFlow retracing)
- L2 normalization for cosine similarity
- Batch processing support

**FAISS Indexing** (`src/stage4_indexing/faiss_indexer.py`)
- Flat L2 index (exact search)
- Metadata association (segment IDs, timestamps)
- Index persistence (save/load)

### Test Results

**Unit Tests**: ✅ **10/10 Passed** (100% pass rate)

| Module | Tests | Status |
|--------|-------|--------|
| Segmentation | 3 | ✅ All passed |
| Embedding | 3 | ✅ All passed |
| FAISS Indexing | 4 | ✅ All passed |

**End-to-End Pipeline Test**:
- Input: 92-second audio file
- Output: 92 segments → 92 embeddings → FAISS index
- Validation: Self-match accuracy = 1.0000 (perfect)
- Performance: ~10 minutes total (includes model loading)

**Key Metrics**:
- Segmentation: ~50-100 segments/sec
- Embedding: ~0.15 segments/sec (after model load)
- Search latency: < 1ms per query
- Memory usage: ~600MB peak

### Performance Characteristics

| Stage | Throughput | Notes |
|-------|-----------|-------|
| Segmentation | 50-100 seg/sec | I/O bound |
| Embedding | 0.15 seg/sec | CPU bound, includes model load time |
| Index Construction | 1000 vec/sec | Linear scaling |
| Search (k=5) | 1000 queries/sec | Exhaustive search |

---

## Usage

### Run Complete Pipeline

```bash
python scripts/milestone1_demo.py
```

### Programmatic Usage

```python
from pathlib import Path
from src.stage2_preprocessing import Segmenter
from src.stage3_embedding import EmbeddingGenerator
from src.stage4_indexing import FAISSIndexer

# Initialize
segmenter = Segmenter(segment_length=1.0, sample_rate=44100)
embedder = EmbeddingGenerator(embedding_dim=512, sample_rate=44100)
indexer = FAISSIndexer(embedding_dim=512)

# Process audio
audio_path = Path("data/raw/test_audio.wav")
segments = segmenter.segment_file(audio_path, Path("data/derived/segments"))

# Generate embeddings
segment_paths = [Path(s["path"]) for s in segments]
embeddings = embedder.generate_embeddings_batch(segment_paths)

# Build index and search
import numpy as np
indexer.add_embeddings(np.array(embeddings), segments)
results = indexer.search(embeddings[0], k=5)
```

---

## Troubleshooting

### OpenL3 Installation Issues

**Problem**: `ModuleNotFoundError: No module named 'imp'`  
**Solution**: Already handled in `requirements.txt` with `resampy>=0.4.0`. If issues persist, see `docs/troubleshooting/INSTALL_OPENL3_PYTHON312.md`

### TensorFlow DLL Error (Windows)

**Problem**: `ImportError: DLL load failed`  
**Solution**: Install Visual C++ Redistributables (see Installation step 1) and **restart terminal/IDE**. See `docs/troubleshooting/FIX_TENSORFLOW_DLL.md`

### FAISS AVX2 Warning

**Impact**: Reduced performance, functionality unaffected  
**Note**: System automatically detects and uses AVX2 if available

---

## Documentation

- **Video Demo**: [`milestone1.mp4`](./milestone1.mp4) - Complete pipeline walkthrough
- **Troubleshooting**: `docs/troubleshooting/` - Detailed installation guides
- **Source Code**: `src/` - Implementation details in code comments

---

## Dependencies

Key packages:
- `openl3>=0.4.0` - Audio embedding models
- `tensorflow>=2.15.0` - Deep learning backend
- `faiss-cpu>=1.7.0` - Similarity search
- `librosa>=0.10.0` - Audio processing
- `numpy>=1.24.0`, `soundfile>=0.12.0`

See `requirements.txt` for complete list.

---


## Acknowledgments

- **OpenL3** - MIT (audio embedding models)
- **FAISS** - Facebook AI Research (similarity search)
- **TensorFlow** - Google (deep learning framework)
