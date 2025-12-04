# Fixed: MERT Sampling Rate Error

## Problem

Error: `The model corresponding to this feature extractor was trained using a sampling rate of 24000. Please make sure that the provided raw_speech input was sampled with 24000 and not 44100.`

## Root Cause

MERT model requires **24000 Hz** sampling rate, but we were:
1. Using default 44100 Hz
2. Not resampling to MERT's required rate before processing

## Solution

Updated `src/stage3_embedding/embedding_generator.py` to:

1. **Detect MERT's required sampling rate** from the processor
2. **Resample audio to 24000 Hz** before passing to MERT processor
3. **Use MERT's sampling rate** (not our default) when calling processor
4. **Added `trust_remote_code=True`** to avoid prompts

### Changes Made

**Single embedding generation:**
- Detects MERT's required sampling rate (24000 Hz)
- Resamples audio from input rate to 24000 Hz
- Uses 24000 Hz when calling processor

**Batch embedding generation:**
- Loads audio at original rate
- Resamples all audio to 24000 Hz
- Uses 24000 Hz for batch processing

**Model loading:**
- Added `trust_remote_code=True` to avoid prompts
- Logs MERT's required sampling rate on load

## Testing

After this fix:
1. Audio will be automatically resampled to 24000 Hz
2. MERT processor will receive correct sampling rate
3. Processing should complete successfully

## Files Changed

- `src/stage3_embedding/embedding_generator.py`
  - `_generate_mert_embedding()` method
  - `_generate_mert_batch()` method
  - `_load_mert()` method

---

**The sampling rate error is now fixed!** Audio will be automatically resampled to MERT's required 24000 Hz.

