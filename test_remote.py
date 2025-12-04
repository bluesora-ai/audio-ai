"""Test the deployed API from local machine."""
import requests
import time
import sys
import json
from pathlib import Path

# Configuration
VPS_IP = "78.46.37.169"  # Your VPS IP address
BASE_URL = f"http://{VPS_IP}:8000"
TIMEOUT = 10

def test_health():
    """Test health endpoint."""
    print("="*60)
    print("1. Testing Health Endpoint")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            print(f"✅ Health check passed")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {BASE_URL}")
        print("   Make sure:")
        print("   - VPS is running")
        print("   - API server is started")
        print("   - Firewall allows port 8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_root():
    """Test root endpoint."""
    print("\n" + "="*60)
    print("2. Testing Root Endpoint")
    print("="*60)
    
    try:
        response = requests.get(BASE_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            print(f"✅ Root endpoint OK")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_docs():
    """Test API documentation."""
    print("\n" + "="*60)
    print("3. Testing API Documentation")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=TIMEOUT)
        if response.status_code == 200:
            print(f"✅ API docs available")
            print(f"   Open in browser: {BASE_URL}/docs")
            return True
        else:
            print(f"❌ Docs not available: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_upload(audio_file):
    """Test file upload."""
    print("\n" + "="*60)
    print("4. Testing File Upload")
    print("="*60)
    
    audio_path = Path(audio_file)
    if not audio_path.exists():
        print(f"❌ Audio file not found: {audio_file}")
        return None
    
    try:
        print(f"   Uploading: {audio_file}")
        with open(audio_path, 'rb') as f:
            files = {'file': (audio_path.name, f, 'audio/wav')}
            response = requests.post(
                f"{BASE_URL}/api/v1/provenance-check",
                files=files,
                timeout=TIMEOUT
            )
        
        if response.status_code == 200:
            data = response.json()
            job_id = data.get('job_id')
            print(f"✅ Upload successful")
            print(f"   Job ID: {job_id}")
            print(f"   Status: {data.get('status')}")
            return job_id
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_status(job_id):
    """Check job status."""
    print("\n" + "="*60)
    print("5. Checking Job Status")
    print("="*60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/status/{job_id}",
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            print(f"✅ Status retrieved")
            print(f"   Status: {status}")
            return status
        else:
            print(f"❌ Failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_report(job_id):
    """Get provenance report."""
    print("\n" + "="*60)
    print("6. Getting Provenance Report")
    print("="*60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/reports/{job_id}",
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            report = response.json()
            print(f"✅ Report retrieved")
            print(f"   File ID: {report.get('file_id')}")
            print(f"   Segments: {report.get('summary', {}).get('total_segments', 0)}")
            print(f"   Risk Level: {report.get('summary', {}).get('risk_level', 'unknown')}")
            
            # Save report
            report_file = f"report_{job_id}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"   Saved to: {report_file}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def wait_for_completion(job_id, max_wait=60):
    """Wait for job to complete."""
    print(f"\n   Waiting for processing (max {max_wait}s)...")
    
    for i in range(max_wait):
        status = test_status(job_id)
        if status == "completed":
            print(f"   ✅ Processing completed!")
            return True
        elif status == "failed":
            print(f"   ❌ Processing failed!")
            return False
        elif status == "processing":
            print(f"   ⏳ Still processing... ({i+1}/{max_wait})")
            time.sleep(1)
        else:
            print(f"   ⚠️  Unknown status: {status}")
            time.sleep(1)
    
    print(f"   ⏱️  Timeout after {max_wait} seconds")
    return False

def main():
    """Run all remote tests."""
    print("="*60)
    print("REMOTE API TESTING")
    print("="*60)
    print(f"VPS URL: {BASE_URL}")
    print()
    
    # Check if VPS IP is set
    if VPS_IP == "your-vps-ip":
        print("❌ ERROR: Please set VPS_IP in this script!")
        print("   Edit test_remote.py and change 'your-vps-ip' to your actual VPS IP")
        return 1
    
    results = []
    
    # Test 1: Health
    results.append(test_health())
    if not results[0]:
        print("\n❌ Cannot connect to VPS. Check connection and try again.")
        return 1
    
    # Test 2: Root
    results.append(test_root())
    
    # Test 3: Docs
    results.append(test_docs())
    
    # Test 4: Upload (if audio file provided)
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        job_id = test_upload(audio_file)
        
        if job_id:
            # Test 5: Wait and check status
            completed = wait_for_completion(job_id)
            
            if completed:
                # Test 6: Get report
                results.append(test_report(job_id))
            else:
                print("\n⚠️  Job did not complete, skipping report test")
        else:
            print("\n⚠️  Upload failed, skipping status/report tests")
    else:
        print("\n⚠️  No audio file provided for upload test")
        print("   Usage: python test_remote.py <audio_file.wav>")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

