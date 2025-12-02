"""Audio segmentation module for Milestone 1."""
import soundfile as sf
import numpy as np
from pathlib import Path
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class Segmenter:
    """Segments audio files into fixed-length chunks (1 second for Milestone 1)."""
    
    def __init__(
        self,
        segment_length: float = 0.5,  # Default to 0.5s for Milestone 2
        sample_rate: int = 44100,
        overlap: float = 0.0
    ):
        """
        Initialize segmenter.
        
        Args:
            segment_length: Length of each segment in seconds (default: 0.5 for M2)
            sample_rate: Target sample rate (default: 44100)
            overlap: Overlap between segments in seconds (default: 0.0)
        """
        self.segment_length = segment_length
        self.sample_rate = sample_rate
        self.overlap = overlap
    
    def segment_file(
        self,
        input_path: Path,
        output_dir: Path
    ) -> List[Dict]:
        """
        Segment an audio file into fixed-length chunks.
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory to save segmented audio files
        
        Returns:
            List of segment metadata dictionaries with keys:
            - segment_id: Unique identifier for segment
            - file_id: Original file identifier
            - start: Start time in seconds
            - end: End time in seconds
            - duration: Duration in seconds
            - path: Path to saved segment file
            - sample_rate: Sample rate of segment
            - index: Segment index number
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Load audio file
            data, sr = sf.read(input_path)
            
            # Convert to mono if stereo
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
            
            # Resample if needed
            if sr != self.sample_rate:
                import librosa
                data = librosa.resample(data, orig_sr=sr, target_sr=self.sample_rate)
                sr = self.sample_rate
            
            # Calculate segmentation parameters
            total_samples = len(data)
            segment_samples = int(self.sample_rate * self.segment_length)
            step_samples = int(self.sample_rate * (self.segment_length - self.overlap))
            
            segments = []
            idx = 0
            start_sample = 0
            file_id = input_path.stem
            
            # Create segments
            while start_sample < total_samples:
                end_sample = min(start_sample + segment_samples, total_samples)
                segment_data = data[start_sample:end_sample]
                
                # Track if padding was needed
                was_padded = len(segment_data) < segment_samples
                
                # Pad if segment is shorter than expected (for last segment)
                if was_padded:
                    padding = segment_samples - len(segment_data)
                    segment_data = np.pad(segment_data, (0, padding), mode='constant')
                
                # Calculate timestamps
                start_sec = start_sample / sr
                end_sec = end_sample / sr
                
                # Duration: use segment_length if padded, otherwise actual duration
                duration = self.segment_length if was_padded else (end_sec - start_sec)
                
                # Generate segment filename
                segment_id = f"{file_id}_seg_{idx:04d}"
                segment_filename = f"{segment_id}_{start_sec:.3f}-{end_sec:.3f}.wav"
                segment_path = output_dir / segment_filename
                
                # Save segment
                sf.write(segment_path, segment_data, sr)
                
                # Create metadata
                segment_meta = {
                    "segment_id": segment_id,
                    "file_id": file_id,
                    "start": float(start_sec),
                    "end": float(end_sec),
                    "duration": float(duration),
                    "path": str(segment_path),
                    "sample_rate": sr,
                    "index": idx
                }
                segments.append(segment_meta)
                
                idx += 1
                start_sample += step_samples
            
            logger.info(f"Created {len(segments)} segments from {input_path}")
            return segments
            
        except Exception as e:
            logger.error(f"Error segmenting file {input_path}: {e}")
            raise