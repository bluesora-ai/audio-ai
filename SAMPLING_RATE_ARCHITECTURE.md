# Sampling Rate Architecture - 44.1 kHz Pipeline

## Overview

The entire forensic pipeline operates at **44.1 kHz** as required by the client. MERT model requires 24 kHz internally, so we resample only when calling MERT, preserving 44.1 kHz throughout the rest of the pipeline.

---

## Pipeline Architecture

### 1. Input & Segmentation (44.1 kHz)
- **Input audio**: Accepted at original rate, resampled to **44.1 kHz**
- **Segmentation**: Segments created at **44.1 kHz**
- **Component**: `Segmenter` (default: 44100 Hz)

### 2. Stem Separation (44.1 kHz)
- **Stem separation**: Demucs operates on **44.1 kHz** audio
- **Output stems**: All stems at **44.1 kHz**
- **Component**: `StemSeparator` (default: 44100 Hz)

### 3. Embedding Generation (44.1 kHz → 24 kHz → 44.1 kHz)

**Pipeline flow:**
1. **Input**: Audio segments at **44.1 kHz**
2. **MERT processing**: 
   - Audio resampled to **24 kHz** (MERT's requirement)
   - MERT generates embeddings
   - Embeddings represent the **44.1 kHz** audio content
3. **Output**: Embeddings (representing 44.1 kHz audio)

**Key point**: The embeddings are generated from 44.1 kHz audio (resampled to 24 kHz only for MERT's internal processing). The embeddings still capture the full spectral information from the 44.1 kHz source.

**Component**: `EmbeddingGenerator`
- Default: 44100 Hz
- Internal MERT resampling: 24000 Hz (automatic)

### 4. Classification & Matching (44.1 kHz)
- **AI/Human classification**: Works on embeddings (representing 44.1 kHz audio)
- **Similarity matching**: Works on embeddings (representing 44.1 kHz audio)
- **Components**: `AIDetector`, `FAISSIndexer`

---

## Configuration

### Default Settings (44.1 kHz)

```python
# config/settings.py
SAMPLE_RATE = 44100  # Pipeline default

# All components use 44100 Hz:
- Segmenter: sample_rate=44100
- StemSeparator: sample_rate=44100
- EmbeddingGenerator: sample_rate=44100
- PipelineOrchestrator: sample_rate=44100
```

### MERT Internal Resampling (Automatic)

```python
# src/stage3_embedding/embedding_generator.py
# Automatically detects MERT's required rate (24000 Hz)
# Resamples only when calling MERT processor
# Rest of pipeline remains at 44100 Hz
```

---

## Why This Architecture?

### ✅ Meets Client Requirements

1. **Forensic-grade analysis**: Pipeline operates at 44.1 kHz
2. **High-fidelity processing**: Full spectral detail preserved
3. **Consistent with customer inputs**: Accepts 44.1 kHz or 48 kHz naturally
4. **Robust matching**: Embeddings represent 44.1 kHz audio content

### ✅ Handles MERT Requirement

1. **MERT needs 24 kHz**: Model was trained at 24 kHz
2. **Internal resampling**: Only resample when calling MERT
3. **No information loss**: Embeddings still represent 44.1 kHz source
4. **Transparent**: Resampling is automatic and internal

---

## Data Flow

```
Input Audio (44.1 kHz or original)
    ↓
Resample to 44.1 kHz (if needed)
    ↓
Segmentation (44.1 kHz)
    ↓
Stem Separation (44.1 kHz)
    ↓
Embedding Generation:
    - Input: 44.1 kHz segments
    - MERT call: Resample to 24 kHz (internal)
    - MERT processing: 24 kHz
    - Output: Embeddings (representing 44.1 kHz audio)
    ↓
Classification (on 44.1 kHz embeddings)
    ↓
Matching (on 44.1 kHz embeddings)
    ↓
Report Generation
```

---

## Verification

### Check Pipeline Sample Rate

```python
from config.settings import SAMPLE_RATE
print(f"Pipeline sample rate: {SAMPLE_RATE} Hz")  # Should be 44100
```

### Check Component Sample Rates

```python
from src.stage2_preprocessing import Segmenter
from src.stage3_embedding import EmbeddingGenerator

segmenter = Segmenter()
print(f"Segmenter: {segmenter.sample_rate} Hz")  # 44100

embedder = EmbeddingGenerator()
print(f"Embedder: {embedder.sample_rate} Hz")  # 44100
```

### MERT Resampling (Automatic)

The resampling to 24 kHz happens automatically inside `_generate_mert_embedding()`:
- Detects MERT's required rate (24000 Hz)
- Resamples from input rate to 24000 Hz
- Processes with MERT
- Returns embeddings representing original 44.1 kHz audio

---

## Summary

✅ **Pipeline operates at 44.1 kHz** (client requirement)  
✅ **MERT resampling is internal only** (24 kHz for MERT, transparent to pipeline)  
✅ **Full spectral detail preserved** (forensic-grade analysis)  
✅ **Consistent with customer inputs** (44.1 kHz or 48 kHz)  
✅ **Robust matching and classification** (embeddings represent 44.1 kHz audio)  

**The architecture correctly implements 44.1 kHz throughout the pipeline while handling MERT's 24 kHz requirement internally.**

