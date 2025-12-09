"""API client for communicating with the Audio Provenance API."""
import requests
import time
import os
from pathlib import Path
from typing import Optional, Dict, Callable
from .constants import TIMEOUT, CONNECT_TIMEOUT, MAX_WAIT, BASE_UPLOAD_TIMEOUT, UPLOAD_TIMEOUT_PER_MB, MAX_UPLOAD_TIMEOUT


class UploadCancelledException(Exception):
    """Exception raised when upload is cancelled."""
    pass


class APIClient:
    """Client for interacting with the Audio Provenance API."""
    
    def __init__(self, base_url: str):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip('/')
        # Create a session with proxies explicitly disabled
        # This ensures all requests go directly without using system proxy settings
        # trust_env=False prevents requests from reading HTTP_PROXY/HTTPS_PROXY env vars
        self.session = requests.Session()
        self.session.proxies = {'http': None, 'https': None}
        self.session.trust_env = False  # Don't trust environment proxy variables
        
        # Also clear proxy env vars for this session to be extra safe
        # (This only affects this process, not the system)
        for env_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
            os.environ.pop(env_var, None)
    
    def test_health(self) -> Dict:
        """
        Test API health endpoint.
        
        Returns:
            Response data as dictionary
        """
        response = self.session.get(
            f"{self.base_url}/health", 
            timeout=CONNECT_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    
    def upload_file(
        self,
        file_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        cancellation_check: Optional[Callable[[], bool]] = None
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
                # Check for cancellation
                if cancellation_check and cancellation_check():
                    raise UploadCancelledException("Upload cancelled by user")
                
                if progress_callback:
                    progress_callback(monitor.bytes_read, file_size)
            
            with open(file_path, 'rb') as f:
                encoder = MultipartEncoder(
                    fields={'file': (file_path.name, f, 'audio/wav')}
                )
                monitor = MultipartEncoderMonitor(encoder, monitor_callback)
                
                headers = {'Content-Type': monitor.content_type}
                
                # Check for cancellation before starting request
                if cancellation_check and cancellation_check():
                    raise UploadCancelledException("Upload cancelled by user")
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/provenance-check",
                    data=monitor,
                    headers=headers,
                    timeout=dynamic_timeout
                )
            
            # Check for cancellation after request completes
            if cancellation_check and cancellation_check():
                raise UploadCancelledException("Upload cancelled by user")
            
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
                        # Check for cancellation during encoding
                        if cancellation_check and cancellation_check():
                            raise UploadCancelledException("Upload cancelled by user")
                        
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
            
            # Check for cancellation before encoding
            if cancellation_check and cancellation_check():
                raise UploadCancelledException("Upload cancelled by user")
            
            data, content_type = encode_multipart()
            headers = {'Content-Type': content_type}
            
            # Check for cancellation before sending request
            if cancellation_check and cancellation_check():
                raise UploadCancelledException("Upload cancelled by user")
            
            response = self.session.post(
                f"{self.base_url}/api/v1/provenance-check",
                data=data,
                headers=headers,
                timeout=dynamic_timeout
            )
            
            # Check for cancellation after request completes
            if cancellation_check and cancellation_check():
                raise UploadCancelledException("Upload cancelled by user")
            
            # Final progress update
            if progress_callback:
                progress_callback(file_size, file_size)
        
        except UploadCancelledException:
            # Re-raise cancellation exception
            raise
        
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
        response = self.session.get(
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
        response = self.session.get(
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

