"""Stem separation module using Demucs for Milestone 2."""
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import logging
import soundfile as sf
import shutil
import tempfile
import os

logger = logging.getLogger(__name__)

# Lazy imports for torch to avoid DLL errors on Windows
HAS_TORCH = False
HAS_TORCHAUDIO = False
HAS_DEMUCS = False

try:
    import torch
    import torchaudio
    HAS_TORCH = True
    HAS_TORCHAUDIO = True
except (ImportError, OSError) as e:
    logger.warning(f"torch/torchaudio not available: {e}. Stem separation will use fallback.")
    HAS_TORCH = False
    HAS_TORCHAUDIO = False

# Try to import demucs (only if torch is available)
if HAS_TORCH:
    try:
        import demucs.separate
        from demucs.pretrained import get_model
        HAS_DEMUCS = True
    except ImportError:
        HAS_DEMUCS = False
        logger.warning("demucs not installed. Stem separation will use fallback.")
else:
    HAS_DEMUCS = False


class StemSeparator:
    """Separates audio into stems: vocals, drums, bass, other."""
    
    STEM_TYPES = ["vocals", "drums", "bass", "other"]
    
    def __init__(
        self,
        model_name: str = "htdemucs",
        device: Optional[str] = None,
        sample_rate: int = 44100
    ):
        """
        Initialize stem separator.
        
        Args:
            model_name: Demucs model name (default: "htdemucs")
            device: torch device ("cuda", "cpu", or None for auto)
            sample_rate: Target sample rate (default: 44100)
        """
        self.model_name = model_name
        self.sample_rate = sample_rate
        
        if not HAS_TORCH:
            logger.warning("PyTorch not available. Stem separation will use fallback.")
            self.device = "cpu"
            self.model = None
            self.has_demucs = False
            return
        
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        self.model = None
        self.underlying_model = None  # Store underlying PyTorch model if Separator wrapper
        self.has_demucs = HAS_DEMUCS
        if HAS_DEMUCS:
            try:
                model_obj = get_model(model_name)
                
                # Check if it's a Separator wrapper or raw model
                if hasattr(model_obj, 'model'):
                    # It's a Separator wrapper - get underlying model
                    self.underlying_model = model_obj.model
                    self.model = model_obj  # Keep wrapper for apply_model if needed
                elif hasattr(model_obj, 'apply_model'):
                    # It's a Separator object without .model attribute
                    self.model = model_obj
                    # Try to find underlying model in attributes
                    for attr in ['_model', 'separator', 'net']:
                        if hasattr(model_obj, attr):
                            self.underlying_model = getattr(model_obj, attr)
                            break
                else:
                    # Raw PyTorch model
                    self.underlying_model = model_obj
                    self.model = model_obj
                
                # Move to device and set eval mode
                if self.underlying_model is not None:
                    self.underlying_model.to(self.device)
                    self.underlying_model.eval()
                elif hasattr(self.model, 'to'):
                    self.model.to(self.device)
                if hasattr(self.model, 'eval'):
                    self.model.eval()
                
                logger.info(f"Loaded Demucs model '{model_name}' on {self.device}")
            except Exception as e:
                logger.warning(f"Failed to load Demucs model: {e}. Using fallback.")
                self.has_demucs = False
    
    def separate_file(
        self,
        input_path: Path,
        output_dir: Path,
        stems: Optional[List[str]] = None
    ) -> Dict[str, Path]:
        """
        Separate audio file into stems.
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory to save separated stems
            stems: List of stems to extract (default: all)
        
        Returns:
            Dictionary mapping stem_type -> output_path
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if stems is None:
            stems = self.STEM_TYPES
        
        stem_paths = {}
        
        if self.has_demucs and (self.model is not None or self.underlying_model is not None) and HAS_TORCH:
            try:
                # Check if model is a Separator object (requires apply_model)
                if hasattr(self.model, 'apply_model') and self.underlying_model is None:
                    # Use apply_model for Separator objects (works with file paths)
                    # This is the proper way to use Demucs Separator
                    # Create temp directory for Demucs output
                    temp_dir = tempfile.mkdtemp()
                    try:
                        # Demucs apply_model expects input file and outputs to a directory
                        self.model.apply_model(str(input_path), out=temp_dir)
                        
                        # Demucs creates subdirectories, find the separated files
                        # Output structure: temp_dir/htdemucs/input_name/{stem}.wav
                        demucs_output = Path(temp_dir)
                        for subdir in demucs_output.iterdir():
                            if subdir.is_dir():
                                for stem_file in subdir.rglob("*.wav"):
                                    stem_name = stem_file.stem
                                    if stem_name in stems:
                                        # Copy to our output directory
                                        output_stem_path = output_dir / f"{input_path.stem}_{stem_name}.wav"
                                        shutil.copy2(stem_file, output_stem_path)
                                        stem_paths[stem_name] = output_stem_path
                                break
                        
                        logger.info(f"Separated {input_path} into {len(stem_paths)} stems using Demucs apply_model")
                    finally:
                        # Clean up temp directory
                        shutil.rmtree(temp_dir, ignore_errors=True)
                
                elif self.underlying_model is not None:
                    # Use underlying PyTorch model directly
                    import torchaudio
                    wav, sr = torchaudio.load(str(input_path))
                    wav = wav.mean(dim=0)  # Convert to mono if stereo
                    
                    # Resample if needed
                    if sr != self.sample_rate:
                        resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
                        wav = resampler(wav)
                    
                    # Ensure correct shape: [batch, channels, samples]
                    if len(wav.shape) == 1:
                        wav = wav.unsqueeze(0)  # Add channel dimension
                    wav = wav.unsqueeze(0).to(self.device)  # Add batch dimension
                    
                    # Separate using the underlying model
                    with torch.no_grad():
                        sources = self.underlying_model(wav)
                    
                    # Demucs returns: [batch, sources, channels, samples]
                    # Sources order: [drums, bass, other, vocals]
                    source_map = {"drums": 0, "bass": 1, "other": 2, "vocals": 3}
                    
                    file_id = input_path.stem
                    
                    for stem_type in stems:
                        if stem_type in source_map:
                            idx = source_map[stem_type]
                            stem_audio = sources[0, idx].cpu().squeeze(0).numpy()
                            
                            # Save stem
                            stem_filename = f"{file_id}_{stem_type}.wav"
                            stem_path = output_dir / stem_filename
                            sf.write(str(stem_path), stem_audio, self.sample_rate)
                            stem_paths[stem_type] = stem_path
                    
                    logger.info(f"Separated {input_path} into {len(stem_paths)} stems using underlying model")
                else:
                    # No usable model, use fallback
                    return self._fallback_separation(input_path, output_dir, stems)
                
            except Exception as e:
                logger.error(f"Error in Demucs separation: {e}")
                # Fallback to mono copy
                return self._fallback_separation(input_path, output_dir, stems)
        else:
            # Fallback: return mono copy for all stems
            return self._fallback_separation(input_path, output_dir, stems)
        
        return stem_paths
    
    def _fallback_separation(
        self,
        input_path: Path,
        output_dir: Path,
        stems: List[str]
    ) -> Dict[str, Path]:
        """Fallback: copy mono audio as all stems."""
        logger.warning("Using fallback separation (mono copy for all stems)")
        
        import soundfile as sf
        data, sr = sf.read(input_path)
        
        # Convert to mono
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
        
        # Resample if needed
        if sr != self.sample_rate:
            import librosa
            data = librosa.resample(data, orig_sr=sr, target_sr=self.sample_rate)
        
        file_id = input_path.stem
        stem_paths = {}
        
        for stem_type in stems:
            stem_filename = f"{file_id}_{stem_type}.wav"
            stem_path = output_dir / stem_filename
            sf.write(str(stem_path), data, self.sample_rate)
            stem_paths[stem_type] = stem_path
        
        return stem_paths
    
    def separate_segment(
        self,
        segment_audio: np.ndarray,
        sample_rate: int,
        stems: Optional[List[str]] = None
    ) -> Dict[str, np.ndarray]:
        """
        Separate a segment (numpy array) into stems.
        
        For small segments (typically 0.5s), we use fallback (same audio for all stems)
        since Demucs Separator.apply_model() requires file paths and is inefficient
        for processing many small segments. Real stem separation is performed on
        full files via separate_file().
        
        Args:
            segment_audio: Audio array (1D)
            sample_rate: Sample rate of audio
            stems: List of stems to extract
        
        Returns:
            Dictionary mapping stem_type -> audio_array
        """
        if stems is None:
            stems = self.STEM_TYPES
        
        # For segments, use fallback (efficient for small audio chunks)
        # Full files use real Demucs separation via separate_file()
        stems_dict = {}
        for stem_type in stems:
            # Return copy of segment audio for all stems
            stems_dict[stem_type] = segment_audio.copy()
        
        return stems_dict