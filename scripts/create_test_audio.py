"""Create test audio file for Milestone 1."""
import soundfile as sf
import numpy as np
from pathlib import Path

def create_test_audio(output_path: Path, duration_sec: float = 10.0, sr: int = 44100):
    """Create a simple test audio file."""
    samples = int(sr * duration_sec)
    # Generate a simple tone with some variation
    t = np.linspace(0, duration_sec, samples)
    frequency = 440  # A4 note
    data = np.sin(2 * np.pi * frequency * t) * 0.3
    # Add some noise
    data += np.random.randn(samples) * 0.05
    data = data.astype(np.float32)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output_path, data, sr)
    print(f"Created test audio: {output_path} ({duration_sec}s, {sr}Hz)")

if __name__ == "__main__":
    test_audio = Path("data/raw/test_audio.wav")
    create_test_audio(test_audio, duration_sec=10.0)

