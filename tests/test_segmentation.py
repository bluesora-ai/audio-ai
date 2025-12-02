"""Tests for segmentation module."""
import pytest
from pathlib import Path
import soundfile as sf
import numpy as np
from src.stage2_preprocessing import Segmenter


def create_test_audio(output_path: Path, duration_sec: float = 5.0, sr: int = 44100):
    """Create a test audio file."""
    samples = int(sr * duration_sec)
    data = np.random.randn(samples).astype(np.float32) * 0.1  # Scale down to avoid clipping
    sf.write(output_path, data, sr)


def test_segmentation_basic(tmp_path):
    """Test basic segmentation of 5-second audio into 1-second segments."""
    # Create test audio
    test_audio = tmp_path / "test.wav"
    create_test_audio(test_audio, duration_sec=5.0)
    
    # Segment
    segmenter = Segmenter(segment_length=1.0, sample_rate=44100)
    output_dir = tmp_path / "segments"
    segments = segmenter.segment_file(test_audio, output_dir)
    
    # Verify
    assert len(segments) == 5, f"Expected 5 segments, got {len(segments)}"
    assert all(abs(s["duration"] - 1.0) < 0.01 for s in segments), "All segments should be ~1 second"
    assert all(Path(s["path"]).exists() for s in segments), "All segment files should exist"
    assert all(s["sample_rate"] == 44100 for s in segments), "All segments should be 44.1kHz"


def test_segmentation_short_file(tmp_path):
    """Test segmentation of short file (< 1 second) - should pad to 1 second."""
    test_audio = tmp_path / "short.wav"
    create_test_audio(test_audio, duration_sec=0.5)
    
    segmenter = Segmenter(segment_length=1.0)
    output_dir = tmp_path / "segments"
    segments = segmenter.segment_file(test_audio, output_dir)
    
    assert len(segments) == 1, "Short file should produce 1 segment"
    assert abs(segments[0]["duration"] - 1.0) < 0.01, "Segment should be padded to 1 second"


def test_segmentation_stereo(tmp_path):
    """Test segmentation handles stereo audio correctly."""
    test_audio = tmp_path / "stereo.wav"
    samples = 44100 * 3  # 3 seconds
    stereo_data = np.random.randn(samples, 2).astype(np.float32) * 0.1
    sf.write(test_audio, stereo_data, 44100)
    
    segmenter = Segmenter(segment_length=1.0)
    output_dir = tmp_path / "segments"
    segments = segmenter.segment_file(test_audio, output_dir)
    
    assert len(segments) == 3, "Should create 3 segments from 3-second audio"
    # Verify segments are mono
    for seg in segments:
        data, sr = sf.read(seg["path"])
        assert len(data.shape) == 1, "Segments should be mono"