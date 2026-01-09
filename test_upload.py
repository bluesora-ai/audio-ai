"""Test script to verify upload functionality."""
import requests
import json
import time
from pathlib import Path

API_URL = "http://148.251.88.48:8000"

def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_upload():
    """Test file upload."""
    print("\nTesting file upload...")
    
    # Use a test audio file if available
    test_file = Path("data/raw/test_audio.wav")
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        print("Please ensure test_audio.wav exists in data/raw/")
        return False
    
    print(f"Uploading: {test_file}")
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file.name, f, 'audio/wav')}
            response = requests.post(
                f"{API_URL}/api/v1/provenance-check",
                files=files,
                timeout=60
            )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            job_id = response.json().get('job_id')
            print(f"\nJob ID: {job_id}")
            print("Waiting 5 seconds before checking status...")
            time.sleep(5)
            
            # Check status
            status_response = requests.get(f"{API_URL}/api/v1/status/{job_id}")
            print(f"\nStatus check:")
            print(f"  Status: {status_response.status_code}")
            print(f"  Response: {json.dumps(status_response.json(), indent=2)}")
            
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Upload Test Script")
    print("=" * 50)
    
    if test_health():
        print("\n✅ Health check passed")
        test_upload()
    else:
        print("\n❌ Health check failed")
        print("Please ensure the server is running and accessible")
