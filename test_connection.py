"""Quick connection diagnostic tool."""
import requests
import sys
import socket
from urllib.parse import urlparse

VPS_IP = "78.46.37.169"
PORT = 8000
BASE_URL = f"http://{VPS_IP}:{PORT}"

def test_ping():
    """Test basic connectivity."""
    print("="*60)
    print("1. Testing Basic Connectivity (Ping)")
    print("="*60)
    try:
        import subprocess
        result = subprocess.run(
            ["ping", "-n", "4", VPS_IP] if sys.platform == "win32" else ["ping", "-c", "4", VPS_IP],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("✅ Ping successful")
            print(result.stdout[:200])
            return True
        else:
            print("❌ Ping failed")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"⚠️  Ping test skipped: {e}")
        return None

def test_port():
    """Test port connectivity."""
    print("\n" + "="*60)
    print("2. Testing Port Connectivity")
    print("="*60)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((VPS_IP, PORT))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {PORT} is open and accessible")
            return True
        else:
            print(f"❌ Port {PORT} is closed or blocked")
            print("   Possible causes:")
            print("   - API server not running")
            print("   - Firewall blocking port")
            print("   - Network issues")
            return False
    except Exception as e:
        print(f"❌ Port test error: {e}")
        return False

def test_http():
    """Test HTTP connection."""
    print("\n" + "="*60)
    print("3. Testing HTTP Connection")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ HTTP connection successful")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ HTTP connection failed: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("❌ HTTP connection timeout (server not responding)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ HTTP connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ HTTP test error: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints."""
    print("\n" + "="*60)
    print("4. Testing API Endpoints")
    print("="*60)
    
    endpoints = [
        ("/", "Root"),
        ("/health", "Health"),
        ("/docs", "Documentation")
    ]
    
    results = []
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {name} endpoint OK")
                results.append(True)
            else:
                print(f"❌ {name} endpoint failed: {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"❌ {name} endpoint error: {e}")
            results.append(False)
    
    return all(results)

def main():
    """Run all diagnostic tests."""
    print("="*60)
    print("VPS CONNECTION DIAGNOSTIC")
    print("="*60)
    print(f"VPS IP: {VPS_IP}")
    print(f"Port: {PORT}")
    print(f"URL: {BASE_URL}")
    print()
    
    results = {}
    
    # Test 1: Ping
    results["Ping"] = test_ping()
    
    # Test 2: Port
    results["Port"] = test_port()
    
    # Test 3: HTTP
    results["HTTP"] = test_http()
    
    # Test 4: API Endpoints
    results["API Endpoints"] = test_api_endpoints()
    
    # Summary
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    
    for test, result in results.items():
        if result is True:
            print(f"✅ {test}: PASS")
        elif result is False:
            print(f"❌ {test}: FAIL")
        else:
            print(f"⚠️  {test}: SKIPPED")
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    if not results.get("Port"):
        print("1. Check if API server is running on VPS:")
        print("   ssh user@78.46.37.169")
        print("   ps aux | grep uvicorn")
        print("   curl http://localhost:8000/health")
    
    if not results.get("HTTP"):
        print("2. Check firewall on VPS:")
        print("   sudo ufw status")
        print("   sudo ufw allow 8000/tcp")
    
    if not results.get("API Endpoints"):
        print("3. Restart API server on VPS:")
        print("   cd ~/audio-ai")
        print("   source venv/bin/activate")
        print("   uvicorn api.main:app --host 0.0.0.0 --port 8000")
    
    if all(results.values()):
        print("✅ All tests passed! Connection is working.")
        return 0
    else:
        print("❌ Some tests failed. Review recommendations above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

