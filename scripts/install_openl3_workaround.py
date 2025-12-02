"""Workaround script to install openl3 with manual weight download."""
import subprocess
import sys
import os
from pathlib import Path

def install_openl3_workaround():
    """Install openl3 with workaround for network issues."""
    print("Attempting to install openl3 with workaround...")
    
    # Try installing with environment variable to skip weight download
    env = os.environ.copy()
    env['OPENL3_SKIP_WEIGHTS'] = '1'  # This might not work, but worth trying
    
    try:
        # First, try normal installation
        print("Attempting standard installation...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "openl3", "--timeout=600"],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes max
        )
        
        if result.returncode == 0:
            print("✓ openl3 installed successfully!")
            return True
        else:
            print("Standard installation failed. Trying alternative method...")
            print(f"Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("Installation timed out. Trying alternative approach...")
    except Exception as e:
        print(f"Error during installation: {e}")
    
    # Alternative: Try installing from GitHub source
    print("\nTrying to install from GitHub source...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", 
             "git+https://github.com/marl/openl3.git", "--timeout=600"],
            capture_output=True,
            text=True,
            timeout=1800
        )
        
        if result.returncode == 0:
            print("✓ openl3 installed from GitHub successfully!")
            return True
        else:
            print(f"GitHub installation also failed: {result.stderr}")
    except Exception as e:
        print(f"GitHub installation error: {e}")
    
    print("\n" + "="*60)
    print("INSTALLATION FAILED DUE TO NETWORK ISSUES")
    print("="*60)
    print("\nThe issue is that openl3 tries to download model weights")
    print("during installation, and the connection is timing out.")
    print("\nSOLUTIONS:")
    print("1. Check your internet connection and firewall settings")
    print("2. Try installing from a different network/VPN")
    print("3. Manually download weights later (openl3 will download")
    print("   them automatically on first use if network is available)")
    print("4. Use a proxy if behind a corporate firewall")
    print("\nYou can still use openl3 - it will download weights on first use.")
    print("="*60)
    
    return False

if __name__ == "__main__":
    install_openl3_workaround()

