"""Stem separation module using Demucs for Milestone 2."""
import torch
import torchaudio
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import logging
import soundfile as sf

logger = logging.getLogger(__name__)

# Try to import demucs
try:
    import demucs.separate
    from demucs.pretrained import get_model
    HAS_DEMUCS = True
except ImportError:
    HAS_DEMUCS = False
    logger.warning("demucs not installed. Stem separation will use fallback.")


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
        
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        self.model = None
        self.has_demucs = HAS_DEMUCS
        if HAS_DEMUCS:
            try:
                self.model = get_model(model_name)
                self.model.to(self.device)
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
        
        if self.has_demucs and self.model is not None:
            try:
                # Load audio
                wav, sr = torchaudio.load(str(input_path))
                wav = wav.mean(dim=0)  # Convert to mono if stereo
                
                # Resample if needed
                if sr != self.sample_rate:
                    resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
                    wav = resampler(wav)
                
                # Add batch dimension
                wav = wav.unsqueeze(0).to(self.device)
                
                # Separate
                with torch.no_grad():
                    sources = self.model(wav)
                
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
                
                logger.info(f"Separated {input_path} into {len(stem_paths)} stems")
                
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
        
        Args:
            segment_audio: Audio array (1D)
            sample_rate: Sample rate of audio
            stems: List of stems to extract
        
        Returns:
            Dictionary mapping stem_type -> audio_array
        """
        if stems is None:
            stems = self.STEM_TYPES
        
        # Convert to tensor
        wav = torch.from_numpy(segment_audio).float()
        if len(wav.shape) == 1:
            wav = wav.unsqueeze(0)
        
        # Resample if needed
        if sample_rate != self.sample_rate:
            resampler = torchaudio.transforms.Resample(sample_rate, self.sample_rate)
            wav = resampler(wav)
        
        wav = wav.unsqueeze(0).to(self.device)
        
        stems_dict = {}
        
        if self.has_demucs and self.model is not None:
            try:
                with torch.no_grad():
                    sources = self.model(wav)
                
                source_map = {"drums": 0, "bass": 1, "other": 2, "vocals": 3}
                
                for stem_type in stems:
                    if stem_type in source_map:
                        idx = source_map[stem_type]
                        stem_audio = sources[0, idx].cpu().squeeze(0).numpy()
                        stems_dict[stem_type] = stem_audio
            except Exception as e:
                logger.error(f"Error separating segment: {e}")
                # Fallback: return same audio for all stems
                for stem_type in stems:
                    stems_dict[stem_type] = segment_audio
        else:
            # Fallback
            for stem_type in stems:
                stems_dict[stem_type] = segment_audio
        
        return stems_dict