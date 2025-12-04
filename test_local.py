"""Complete local testing script - Test all components before deployment."""
import sys
from pathlib import Path
import subprocess

def run_test(name, command):
    """Run a test command and report result."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print('='*60)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print(f"✅ {name}: PASSED")
            if result.stdout:
                print(result.stdout[:500])  # Print first 500 chars
            return True
        else:
            print(f"❌ {name}: FAILED")
            print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏱️ {name}: TIMEOUT (took too long)")
        return False
    except Exception as e:
        print(f"❌ {name}: ERROR - {e}")
        return False

def main():
    """Run all local tests."""
    print("="*60)
    print("LOCAL TESTING - Audio Provenance System")
    print("="*60)
    
    results = []
    
    # Test 1: Check Python version
    print("\n1. Checking Python version...")
    version_result = subprocess.run(
        "python --version",
        shell=True,
        capture_output=True,
        text=True
    )
    print(f"   {version_result.stdout.strip()}")
    
    # Test 2: Check virtual environment
    print("\n2. Checking virtual environment...")
    venv_result = subprocess.run(
        "python -c \"import sys; print('venv' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 'no venv')\"",
        shell=True,
        capture_output=True,
        text=True
    )
    venv_status = venv_result.stdout.strip()
    if 'venv' in venv_status:
        print("   ✅ Virtual environment is active")
    else:
        print("   ⚠️  Virtual environment not detected (activate it first)")
    
    # Test 3: Check imports
    results.append(run_test(
        "Module Imports",
        "python -c \"from src.pipeline import PipelineOrchestrator; print('All imports OK')\""
    ))
    
    # Test 4: Create test audio
    results.append(run_test(
        "Create Test Audio",
        "python scripts/create_test_audio.py"
    ))
    
    # Test 5: Run Milestone 1 demo
    results.append(run_test(
        "Milestone 1 Demo",
        "python scripts/milestone1_demo.py"
    ))
    
    # Test 6: Check outputs
    print("\n" + "="*60)
    print("Checking Generated Files")
    print("="*60)
    
    files_to_check = [
        ("Segments", "data/derived/segments/*.wav"),
        ("Embeddings", "data/embeddings/*.npy"),
        ("FAISS Index", "data/indexes/faiss_index.bin"),
        ("Test Audio", "data/raw/test_audio.wav")
    ]
    
    for name, pattern in files_to_check:
        import glob
        files = glob.glob(pattern)
        if files:
            print(f"✅ {name}: Found {len(files)} file(s)")
        else:
            print(f"❌ {name}: Not found")
            results.append(False)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - Ready for deployment!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed - Fix issues before deployment")
        return 1

if __name__ == "__main__":
    sys.exit(main())

