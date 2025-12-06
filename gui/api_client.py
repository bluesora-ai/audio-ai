"""API client for communicating with the Audio Provenance API."""
import requests
import time
from pathlib import Path
from typing import Optional, Dict, Callable
from .constants import TIMEOUT, CONNECT_TIMEOUT, MAX_WAIT, BASE_UPLOAD_TIMEOUT, UPLOAD_TIMEOUT_PER_MB, MAX_UPLOAD_TIMEOUT


class APIClient:
    """Client for interacting with the Audio Provenance API."""
    
    def __init__(self, base_url: str):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip('/')
    
    def test_health(self) -> Dict:
        """
        Test API health endpoint.
        
        Returns:
            Response data as dictionary
        """
        response = requests.get(f"{self.base_url}/health", timeout=CONNECT_TIMEOUT)
        response.raise_for_status()
        return response.json()
    
    def upload_file(
        self,
        file_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict:
        """
        Upload audio file for provenance checking.
        
        Args:
            file_path: Path to audio file
            progress_callback: Optional callback(uploaded_bytes, total_bytes) for progress updates
        
        Returns:
            Response data with job_id
        """
        file_size = file_path.stat().st_size
        dynamic_timeout = min(
            BASE_UPLOAD_TIMEOUT + ((file_size / (1024 * 1024)) * UPLOAD_TIMEOUT_PER_MB),
            MAX_UPLOAD_TIMEOUT
        )
        
        # Use requests-toolbelt for proper streaming upload with progress
        try:
            from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor
            
            def monitor_callback(monitor):
                if progress_callback:
                    progress_callback(monitor.bytes_read, file_size)
            
            with open(file_path, 'rb') as f:
                encoder = MultipartEncoder(
                    fields={'file': (file_path.name, f, 'audio/wav')}
                )
                monitor = MultipartEncoderMonitor(encoder, monitor_callback)
                
                headers = {'Content-Type': monitor.content_type}
                response = requests.post(
                    f"{self.base_url}/api/v1/provenance-check",
                    data=monitor,
                    headers=headers,
                    timeout=dynamic_timeout
                )
            
            # Final progress update
            if progress_callback:
                progress_callback(file_size, file_size)
            
        except ImportError:
            # Fallback: Manual multipart encoding
            import io
            
            boundary = '----WebKitFormBoundary' + ''.join([str(i) for i in range(15)])
            CRLF = b'\r\n'
            
            def encode_multipart():
                body_parts = []
                body_parts.append(f'--{boundary}'.encode())
                body_parts.append(CRLF)
                body_parts.append(f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"'.encode())
                body_parts.append(CRLF)
                body_parts.append(b'Content-Type: audio/wav')
                body_parts.append(CRLF)
                body_parts.append(CRLF)
                
                chunk_size = 64 * 1024  # 64KB chunks
                uploaded = 0
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        body_parts.append(chunk)
                        uploaded += len(chunk)
                        if progress_callback:
                            progress_callback(uploaded, file_size)
                
                body_parts.append(CRLF)
                body_parts.append(f'--{boundary}--'.encode())
                body_parts.append(CRLF)
                
                return b''.join(body_parts), f'multipart/form-data; boundary={boundary}'
            
            data, content_type = encode_multipart()
            headers = {'Content-Type': content_type}
            response = requests.post(
                f"{self.base_url}/api/v1/provenance-check",
                data=data,
                headers=headers,
                timeout=dynamic_timeout
            )
            
            # Final progress update
            if progress_callback:
                progress_callback(file_size, file_size)
        
        response.raise_for_status()
        return response.json()
    
    def get_status(self, job_id: str) -> Dict:
        """
        Get status of a provenance check job.
        
        Args:
            job_id: Job ID from upload response
        
        Returns:
            Status data as dictionary
        """
        response = requests.get(
            f"{self.base_url}/api/v1/status/{job_id}",
            timeout=CONNECT_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    
    def get_report(self, job_id: str) -> Dict:
        """
        Download provenance report for a completed job.
        
        Args:
            job_id: Job ID from upload response
        
        Returns:
            Report data as dictionary
        """
        response = requests.get(
            f"{self.base_url}/api/v1/reports/{job_id}",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(
        self,
        job_id: str,
        status_callback: Optional[Callable[[str], None]] = None,
        max_wait: int = MAX_WAIT
    ) -> Dict:
        """
        Wait for job to complete, polling status endpoint.
        
        Args:
            job_id: Job ID to wait for
            status_callback: Optional callback(status) for status updates
            max_wait: Maximum seconds to wait
        
        Returns:
            Final status data
        """
        start_time = time.time()
        
        while True:
            status_data = self.get_status(job_id)
            status = status_data.get('status')
            
            if status_callback:
                status_callback(status)
            
            if status == "completed":
                return status_data
            elif status == "failed":
                raise Exception(f"Processing failed: {status_data.get('error', 'Unknown error')}")
            
            if time.time() - start_time > max_wait:
                raise TimeoutError(f"Timeout after {max_wait}s")
            
            # Adaptive polling
            sleep_time = 2 if status == "processing" else 5
            time.sleep(sleep_time)

