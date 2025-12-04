"""Complete VPS testing suite - Verify all functionality from local machine."""
import requests
import time
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
import hashlib

# Configuration
VPS_IP = "78.46.37.169"  # Your VPS IP
BASE_URL = f"http://{VPS_IP}:8000"
TIMEOUT = 120  # 2 minutes for upload/processing
CONNECT_TIMEOUT = 10  # 10 seconds for connection
MAX_WAIT = 600  # 10 minutes max wait for processing

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text):
    print(f"   {text}")

def test_health():
    """Test 1: Health endpoint."""
    print_header("TEST 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=CONNECT_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_success("Health check passed")
            print_info(f"Response: {data}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Cannot connect to VPS: {e}")
        print_info("Make sure:")
        print_info("  - VPS is running")
        print_info("  - API server is started: uvicorn api.main:app --host 0.0.0.0 --port 8000")
        print_info("  - Firewall allows port 8000: sudo ufw allow 8000/tcp")
        return False

def test_api_info():
    """Test 2: API info endpoints."""
    print_header("TEST 2: API Information")
    results = []
    
    # Root endpoint
    try:
        response = requests.get(BASE_URL, timeout=CONNECT_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_success("Root endpoint OK")
            print_info(f"API: {data.get('message')}")
            print_info(f"Status: {data.get('status')}")
            results.append(True)
        else:
            print_error(f"Root endpoint failed: {response.status_code}")
            results.append(False)
    except Exception as e:
        print_error(f"Root endpoint error: {e}")
        results.append(False)
    
    # Docs endpoint
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=CONNECT_TIMEOUT)
        if response.status_code == 200:
            print_success("API documentation available")
            print_info(f"Open in browser: {BASE_URL}/docs")
            results.append(True)
        else:
            print_warning(f"Docs endpoint: {response.status_code}")
            results.append(False)
    except Exception as e:
        print_warning(f"Docs endpoint error: {e}")
        results.append(False)
    
    return all(results)

def upload_audio(audio_file: Path) -> Optional[str]:
    """Test 3: Upload audio file."""
    print_header("TEST 3: Upload Audio File")
    
    if not audio_file.exists():
        print_error(f"Audio file not found: {audio_file}")
        return None
    
    file_size = audio_file.stat().st_size / (1024 * 1024)  # MB
    print_info(f"File: {audio_file.name}")
    print_info(f"Size: {file_size:.2f} MB")
    
    try:
        with open(audio_file, 'rb') as f:
            files = {'file': (audio_file.name, f, 'audio/wav')}
            print_info("Uploading...")
            response = requests.post(
                f"{BASE_URL}/api/v1/provenance-check",
                files=files,
                timeout=TIMEOUT,
                stream=True  # Stream upload for large files
            )
        
        if response.status_code == 200:
            data = response.json()
            job_id = data.get('job_id')
            status = data.get('status')
            print_success("Upload successful")
            print_info(f"Job ID: {job_id}")
            print_info(f"Status: {status}")
            return job_id
        else:
            print_error(f"Upload failed: {response.status_code}")
            print_info(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Upload error: {e}")
        return None

def wait_for_completion(job_id: str) -> bool:
    """Test 4: Wait for processing to complete."""
    print_header("TEST 4: Processing Status")
    print_info(f"Job ID: {job_id}")
    print_info(f"Waiting for completion (max {MAX_WAIT}s)...")
    
    start_time = time.time()
    last_status = None
    
    for i in range(MAX_WAIT):
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/status/{job_id}",
                timeout=CONNECT_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                
                if status != last_status:
                    print_info(f"Status: {status}")
                    last_status = status
                
                if status == "completed":
                    elapsed = time.time() - start_time
                    print_success(f"Processing completed in {elapsed:.1f}s")
                    return True
                elif status == "failed":
                    error = data.get('error', 'Unknown error')
                    print_error(f"Processing failed: {error}")
                    return False
                elif status == "processing":
                    if i % 10 == 0:  # Print every 10 seconds
                        elapsed = time.time() - start_time
                        print_info(f"Still processing... ({elapsed:.1f}s elapsed)")
            else:
                print_warning(f"Status check failed: {response.status_code}")
            
            time.sleep(1)
        except Exception as e:
            print_warning(f"Status check error: {e}")
            time.sleep(1)
    
    print_error(f"Timeout after {MAX_WAIT} seconds")
    return False

def download_and_verify_report(job_id: str) -> Optional[Dict]:
    """Test 5: Download and verify provenance report."""
    print_header("TEST 5: Download Provenance Report")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/reports/{job_id}",
            timeout=TIMEOUT  # Reports can be large
        )
        
        if response.status_code == 200:
            report = response.json()
            
            # Save report
            report_dir = Path("test_reports")
            report_dir.mkdir(exist_ok=True)
            report_file = report_dir / f"report_{job_id}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print_success("Report downloaded")
            print_info(f"Saved to: {report_file}")
            
            # Verify report structure
            return verify_report_structure(report, job_id)
        else:
            print_error(f"Failed to download report: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Download error: {e}")
        return None

def verify_report_structure(report: Dict, job_id: str) -> bool:
    """Verify provenance report has all required fields."""
    print_header("TEST 6: Verify Report Structure")
    
    required_fields = [
        'file_id',
        'timestamp',
        'summary',
        'segments',
        'model_provenance',
        'index_provenance'
    ]
    
    missing = []
    for field in required_fields:
        if field not in report:
            missing.append(field)
    
    if missing:
        print_error(f"Missing required fields: {missing}")
        return False
    
    print_success("All required fields present")
    
    # Verify summary
    summary = report.get('summary', {})
    print_info(f"Total segments: {summary.get('total_segments', 0)}")
    print_info(f"Risk level: {summary.get('risk_level', 'unknown')}")
    print_info(f"AI probability: {summary.get('ai_probability', 0):.3f}")
    
    # Verify segments
    segments = report.get('segments', [])
    if segments:
        first_seg = segments[0]
        print_info(f"First segment ID: {first_seg.get('segment_id', 'N/A')}")
        print_info(f"First segment AI prob: {first_seg.get('ai_probability', 0):.3f}")
        
        # Check for matches
        matches = first_seg.get('matches', [])
        if matches:
            print_info(f"Top match similarity: {matches[0].get('similarity', 0):.3f}")
        else:
            print_warning("No matches found in first segment")
    
    # Verify provenance
    model_prov = report.get('model_provenance', {})
    print_info(f"Embedding model: {model_prov.get('model_name', 'N/A')}")
    print_info(f"Model version: {model_prov.get('model_version', 'N/A')}")
    
    index_prov = report.get('index_provenance', {})
    print_info(f"Index type: {index_prov.get('index_type', 'N/A')}")
    print_info(f"Index vectors: {index_prov.get('total_vectors', 0)}")
    
    return True

def test_robustness(audio_file: Path):
    """Test 7: Robustness - test with different audio formats."""
    print_header("TEST 7: Robustness Testing")
    print_warning("Robustness testing requires multiple audio formats")
    print_info("This test verifies the system handles:")
    print_info("  - Different audio formats (WAV, MP3, etc.)")
    print_info("  - Different sample rates")
    print_info("  - Different bitrates")
    print_info("  - Transformed audio (pitch-shifted, time-stretched)")
    print_info("\nFor full robustness testing, use: python test_robustness.py")

def generate_test_summary(results: Dict):
    """Generate final test summary."""
    print_header("TEST SUMMARY")
    
    total_tests = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total_tests - passed
    
    print_info(f"Total Tests: {total_tests}")
    print_success(f"Passed: {passed}") if passed > 0 else None
    print_error(f"Failed: {failed}") if failed > 0 else None
    
    print("\n" + "="*70)
    print("DETAILED RESULTS:")
    print("="*70)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print("\n" + "="*70)
    
    if passed == total_tests:
        print_success("ALL TESTS PASSED - System is working correctly!")
        return 0
    else:
        print_error(f"{failed} test(s) failed - Review errors above")
        return 1

def main():
    """Run complete test suite."""
    print_header("VPS COMPLETE TEST SUITE")
    print_info(f"VPS URL: {BASE_URL}")
    print_info(f"Testing from: {Path.cwd()}")
    
    results = {}
    
    # Test 1: Health
    results["Health Check"] = test_health()
    if not results["Health Check"]:
        print_error("\nCannot connect to VPS. Fix connection issues first.")
        return 1
    
    # Test 2: API Info
    results["API Information"] = test_api_info()
    
    # Test 3-6: Full pipeline (if audio file provided)
    if len(sys.argv) > 1:
        audio_file = Path(sys.argv[1])
        
        if not audio_file.exists():
            print_error(f"Audio file not found: {audio_file}")
            return 1
        
        # Upload
        job_id = upload_audio(audio_file)
        if job_id:
            results["File Upload"] = True
            
            # Wait for completion
            if wait_for_completion(job_id):
                results["Processing"] = True
                
                # Download and verify report
                report_ok = download_and_verify_report(job_id)
                results["Report Download"] = report_ok is not None
                results["Report Structure"] = report_ok if report_ok else False
            else:
                results["Processing"] = False
                results["Report Download"] = False
                results["Report Structure"] = False
        else:
            results["File Upload"] = False
            results["Processing"] = False
            results["Report Download"] = False
            results["Report Structure"] = False
    else:
        print_warning("\nNo audio file provided - skipping pipeline tests")
        print_info("Usage: python test_vps_complete.py <audio_file.wav>")
        results["File Upload"] = None
        results["Processing"] = None
        results["Report Download"] = None
        results["Report Structure"] = None
    
    # Test 7: Robustness info
    if len(sys.argv) > 1:
        test_robustness(Path(sys.argv[1]))
    
    # Generate summary
    return generate_test_summary(results)

if __name__ == "__main__":
    sys.exit(main())

