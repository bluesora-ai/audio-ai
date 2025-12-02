"""Robustness augmentation pipeline for embedding training."""
import numpy as np
import librosa
import soundfile as sf
from typing import Dict, List, Optional, Callable
import logging
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class AudioAugmentation:
    """Applies robustness augmentations to audio."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize augmentation pipeline.
        
        Args:
            config_path: Path to augmentation config YAML
        """
        self.augmentations = []
        self.config = self._load_config(config_path)
        self._build_pipeline()
    
    def _load_config(self, config_path: Optional[Path]) -> Dict:
        """Load augmentation config from YAML."""
        default_config = {
            "lossy_encoding": {"enabled": True, "formats": ["mp3", "aac"], "bitrates": [128, 64, 32]},
            "resampling": {"enabled": True, "rates": [48000, 44100, 22050]},
            "bit_depth": {"enabled": True, "depths": [16, 8]},
            "amplitude": {"enabled": True, "range_db": [-12, 12]},
            "time_stretch": {"enabled": True, "range": [0.85, 1.15]},
            "pitch_shift": {"enabled": True, "range_semitones": [-3, 3]},
            "eq_filtering": {"enabled": True, "types": ["hp", "lp", "bp"]},
            "reverb": {"enabled": True, "room_size": [0.1, 0.9]},
            "noise": {"enabled": True, "snr_db": [10, 30]},
            "cropping": {"enabled": True, "min_duration": 0.25}
        }
        
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}. Using defaults.")
        
        return default_config
    
    def _build_pipeline(self):
        """Build augmentation pipeline from config."""
        if self.config.get("lossy_encoding", {}).get("enabled"):
            self.augmentations.append(self._apply_lossy_encoding)
        
        if self.config.get("resampling", {}).get("enabled"):
            self.augmentations.append(self._apply_resampling)
        
        if self.config.get("amplitude", {}).get("enabled"):
            self.augmentations.append(self._apply_amplitude)
        
        if self.config.get("time_stretch", {}).get("enabled"):
            self.augmentations.append(self._apply_time_stretch)
        
        if self.config.get("pitch_shift", {}).get("enabled"):
            self.augmentations.append(self._apply_pitch_shift)
        
        if self.config.get("eq_filtering", {}).get("enabled"):
            self.augmentations.append(self._apply_eq_filtering)
        
        if self.config.get("reverb", {}).get("enabled"):
            self.augmentations.append(self._apply_reverb)
        
        if self.config.get("noise", {}).get("enabled"):
            self.augmentations.append(self._apply_noise)
        
        if self.config.get("cropping", {}).get("enabled"):
            self.augmentations.append(self._apply_cropping)
    
    def augment(
        self,
        audio: np.ndarray,
        sample_rate: int,
        num_augmentations: int = 1,
        random_seed: Optional[int] = None
    ) -> List[np.ndarray]:
        """
        Apply random augmentations to audio.
        
        Args:
            audio: Audio array
            sample_rate: Sample rate
            num_augmentations: Number of augmented versions to generate
            random_seed: Random seed
        
        Returns:
            List of augmented audio arrays
        """
        if random_seed is not None:
            np.random.seed(random_seed)
        
        augmented = []
        for _ in range(num_augmentations):
            aug_audio = audio.copy()
            aug_sr = sample_rate
            
            # Apply random subset of augmentations
            num_augs = np.random.randint(1, len(self.augmentations) + 1)
            selected = np.random.choice(self.augmentations, num_augs, replace=False)
            
            for aug_func in selected:
                try:
                    aug_audio, aug_sr = aug_func(aug_audio, aug_sr)
                except Exception as e:
                    logger.warning(f"Augmentation failed: {e}")
            
            augmented.append(aug_audio)
        
        return augmented
    
    def _apply_lossy_encoding(self, audio: np.ndarray, sr: int) -> tuple:
        """Simulate lossy encoding (simplified - would need actual encoding)."""
        # Add slight quantization noise
        noise_level = np.random.uniform(0.001, 0.01)
        noise = np.random.normal(0, noise_level, audio.shape)
        return audio + noise, sr
    
    def _apply_resampling(self, audio: np.ndarray, sr: int) -> tuple:
        """Resample audio."""
        rates = self.config["resampling"]["rates"]
        target_sr = np.random.choice(rates)
        if target_sr != sr:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
        return audio, target_sr
    
    def _apply_amplitude(self, audio: np.ndarray, sr: int) -> tuple:
        """Apply amplitude scaling."""
        range_db = self.config["amplitude"]["range_db"]
        gain_db = np.random.uniform(range_db[0], range_db[1])
        gain_linear = 10 ** (gain_db / 20)
        return audio * gain_linear, sr
    
    def _apply_time_stretch(self, audio: np.ndarray, sr: int) -> tuple:
        """Apply time stretching."""
        stretch_range = self.config["time_stretch"]["range"]
        rate = np.random.uniform(stretch_range[0], stretch_range[1])
        audio = librosa.effects.time_stretch(audio, rate=rate)
        return audio, sr
    
    def _apply_pitch_shift(self, audio: np.ndarray, sr: int) -> tuple:
        """Apply pitch shifting."""
        semitone_range = self.config["pitch_shift"]["range_semitones"]
        n_steps = np.random.uniform(semitone_range[0], semitone_range[1])
        audio = librosa.effects.pitch_shift(audio, sr=sr, n_steps=n_steps)
        return audio, sr
    
    def _apply_eq_filtering(self, audio: np.ndarray, sr: int) -> tuple:
        """Apply EQ filtering."""
        filter_type = np.random.choice(self.config["eq_filtering"]["types"])
        
        if filter_type == "hp":  # High-pass
            cutoff = np.random.uniform(100, 2000)
            from scipy import signal
            b, a = signal.butter(4, cutoff / (sr / 2), 'high')
            audio = signal.filtfilt(b, a, audio)
        elif filter_type == "lp":  # Low-pass
            cutoff = np.random.uniform(2000, 8000)
            from scipy import signal
            b, a = signal.butter(4, cutoff / (sr / 2), 'low')
            audio = signal.filtfilt(b, a, audio)
        elif filter_type == "bp":  # Band-pass
            low = np.random.uniform(200, 1000)
            high = np.random.uniform(2000, 6000)
            from scipy import signal
            b, a = signal.butter(4, [low / (sr / 2), high / (sr / 2)], 'band')
            audio = signal.filtfilt(b, a, audio)
        
        return audio, sr
    
    def _apply_reverb(self, audio: np.ndarray, sr: int) -> tuple:
        """Apply reverb (simplified IR convolution)."""
        room_size = np.random.uniform(*self.config["reverb"]["room_size"])
        # Simple delay-based reverb
        delay_samples = int(sr * 0.03 * room_size)
        delayed = np.pad(audio, (delay_samples, 0))[:len(audio)]
        audio = audio + delayed * 0.3 * room_size
        return audio, sr
    
    def _apply_noise(self, audio: np.ndarray, sr: int) -> tuple:
        """Add noise."""
        snr_range = self.config["noise"]["snr_db"]
        snr_db = np.random.uniform(snr_range[0], snr_range[1])
        
        # Calculate noise power
        signal_power = np.mean(audio ** 2)
        noise_power = signal_power / (10 ** (snr_db / 10))
        noise = np.random.normal(0, np.sqrt(noise_power), audio.shape)
        
        return audio + noise, sr
    
    def _apply_cropping(self, audio: np.ndarray, sr: int) -> tuple:
        """Apply random cropping."""
        min_duration = self.config["cropping"]["min_duration"]
        min_samples = int(min_duration * sr)
        
        if len(audio) > min_samples:
            crop_start = np.random.randint(0, len(audio) - min_samples)
            crop_end = crop_start + np.random.randint(min_samples, len(audio) - crop_start)
            audio = audio[crop_start:crop_end]
        
        return audio, sr