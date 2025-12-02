"""Manual installation of openl3 by bypassing weight download during setup."""
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
import urllib.request
import gzip

def download_weights_manually():
    """Manually download openl3 weights with retry logic."""
    weights_urls = [
        "https://github.com/marl/openl3/releases/download/v0.4.0/openl3_audio_linear_music-v0_4_0.h5.gz",
        "https://github.com/marl/openl3/releases/download/v0.4.0/openl3_audio_linear_env-v0_4_0.h5.gz",
        "https://github.com/marl/openl3/releases/download/v0.4.0/openl3_audio_mel128_music-v0_4_0.h5.gz",
        "https://github.com/marl/openl3/releases/download/v0.4.0/openl3_audio_mel128_env-v0_4_0.h5.gz",
    ]
    
    # Get openl3 cache directory
    import platformdirs
    cache_dir = Path(platformdirs.user_cache_dir()) / "openl3"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading weights to: {cache_dir}")
    
    for url in weights_urls:
        filename = url.split("/")[-1]
        output_path = cache_dir / filename
        
        if output_path.exists():
            print(f"✓ {filename} already exists, skipping...")
            continue
            
        print(f"Downloading {filename}...")
        try:
            urllib.request.urlretrieve(url, output_path)
            print(f"✓ Downloaded {filename}")
        except Exception as e:
            print(f"✗ Failed to download {filename}: {e}")
            return False
    
    return True

def install_openl3_without_weights():
    """Install openl3 package without downloading weights."""
    print("Installing openl3 package (without weights)...")
    
    # Create a temporary modified setup.py
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Download source
        print("Downloading openl3 source...")
        subprocess.run([
            sys.executable, "-m", "pip", "download", "--no-deps", 
            "--no-binary", ":all:", "openl3", "-d", str(tmp_path)
        ], check=True)
        
        # Extract
        import tarfile
        tar_file = list(tmp_path.glob("*.tar.gz"))[0]
        extract_dir = tmp_path / "openl3"
        with tarfile.open(tar_file, "r:gz") as tar:
            tar.extractall(tmp_path)
        
        # Modify setup.py to skip weight download
        setup_py = extract_dir / "setup.py"
        if setup_py.exists():
            content = setup_py.read_text()
            # Comment out weight download section
            modified_content = content.replace(
                "download_weights()",
                "# download_weights()  # Skipped - will download on first use"
            )
            setup_py.write_text(modified_content)
            print("Modified setup.py to skip weight download")
        
        # Install from modified source
        print("Installing from modified source...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            str(extract_dir), "--no-deps"
        ], check=True)
    
    print("✓ openl3 package installed!")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("OpenL3 Installation Workaround")
    print("=" * 60)
    
    try:
        # Try to install package first
        install_openl3_without_weights()
        
        # Then try to download weights
        print("\nAttempting to download weights...")
        if download_weights_manually():
            print("\n✓ All weights downloaded successfully!")
        else:
            print("\n⚠ Weight download failed, but package is installed.")
            print("OpenL3 will attempt to download weights on first use.")
        
    except Exception as e:
        print(f"\n✗ Installation failed: {e}")
        print("\nAlternative: Install openl3 when you have better network connectivity.")
        print("The package will work - it will download weights on first use.")

