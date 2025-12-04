"""Desktop GUI application for testing Audio Provenance API."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
import json
import threading
import time
from pathlib import Path
from typing import Optional, Dict

# Configuration
VPS_IP = "78.46.37.169"
BASE_URL = f"http://{VPS_IP}:8000"
TIMEOUT = 600  # 10 minutes for upload (increased for large files)
CONNECT_TIMEOUT = 30  # 30 seconds for connection
MAX_WAIT = 1800  # 30 minutes for processing completion (audio processing can take time)

# Timeout calculation: base timeout + file size factor
# Formula: base_timeout + (file_size_mb * 30 seconds per MB)
BASE_UPLOAD_TIMEOUT = 300  # 5 minutes base
UPLOAD_TIMEOUT_PER_MB = 30  # 30 seconds per MB
MAX_UPLOAD_TIMEOUT = 1800  # 30 minutes maximum

class ProvenanceTestApp:
    """Desktop GUI for testing Audio Provenance API."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Provenance Test App")
        self.root.geometry("900x700")
        
        self.job_id: Optional[str] = None
        self.report: Optional[Dict] = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Audio Provenance Test App", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # VPS URL
        url_frame = ttk.Frame(main_frame)
        url_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(url_frame, text="VPS URL:").pack(side=tk.LEFT, padx=5)
        self.url_var = tk.StringVar(value=BASE_URL)
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=50)
        url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # File selection
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(file_frame, text="Audio File:").pack(side=tk.LEFT, padx=5)
        self.file_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_var, width=50)
        file_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Test Health", command=self.test_health).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Upload & Process", command=self.upload_and_process).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Check Status", command=self.check_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Download Report", command=self.download_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        
        # Status
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        status_frame.columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Arial", 10))
        status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Job ID
        job_frame = ttk.Frame(main_frame)
        job_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(job_frame, text="Job ID:").pack(side=tk.LEFT, padx=5)
        self.job_id_var = tk.StringVar()
        job_entry = ttk.Entry(job_frame, textvariable=self.job_id_var, state='readonly', width=50)
        job_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Log output
        log_frame = ttk.LabelFrame(main_frame, text="Log Output", padding="5")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Report display
        report_frame = ttk.LabelFrame(main_frame, text="Report Summary", padding="5")
        report_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        report_frame.columnconfigure(0, weight=1)
        
        self.report_text = scrolledtext.ScrolledText(report_frame, height=8, width=80)
        self.report_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
    
    def log(self, message: str, level: str = "INFO"):
        """Add message to log."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] [{level}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """Clear log output."""
        self.log_text.delete(1.0, tk.END)
        self.report_text.delete(1.0, tk.END)
        self.status_var.set("Ready")
        self.job_id_var.set("")
        self.job_id = None
        self.report = None
    
    def browse_file(self):
        """Browse for audio file."""
        filename = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio files", "*.wav *.mp3 *.flac *.m4a"), ("All files", "*.*")]
        )
        if filename:
            self.file_var.set(filename)
            self.log(f"Selected file: {filename}")
    
    def test_health(self):
        """Test health endpoint."""
        def run_test():
            self.progress.start()
            self.status_var.set("Testing health...")
            self.log("Testing health endpoint...")
            
            try:
                url = self.url_var.get()
                response = requests.get(f"{url}/health", timeout=CONNECT_TIMEOUT)
                
                if response.status_code == 200:
                    data = response.json()
                    self.log(f"✅ Health check passed: {data}")
                    self.status_var.set("✅ Health check passed")
                    messagebox.showinfo("Success", f"Health check passed!\n{json.dumps(data, indent=2)}")
                else:
                    self.log(f"❌ Health check failed: {response.status_code}")
                    self.status_var.set("❌ Health check failed")
                    messagebox.showerror("Error", f"Health check failed: {response.status_code}")
            except requests.exceptions.Timeout:
                self.log(f"❌ Connection timeout - Server not responding")
                self.status_var.set("❌ Timeout")
                messagebox.showerror("Timeout", 
                    "Connection timeout!\n\n"
                    "Possible causes:\n"
                    "1. API server not running on VPS\n"
                    "2. Firewall blocking connection\n"
                    "3. Network issues\n\n"
                    "Run: python test_connection.py to diagnose")
            except requests.exceptions.ConnectionError as e:
                self.log(f"❌ Connection error: {e}")
                self.status_var.set("❌ Connection Error")
                messagebox.showerror("Connection Error", 
                    f"Cannot connect to VPS!\n\n{e}\n\n"
                    "Check:\n"
                    "1. VPS is running\n"
                    "2. API server is started\n"
                    "3. Firewall allows port 8000\n\n"
                    "Run: python test_connection.py to diagnose")
            except Exception as e:
                self.log(f"❌ Error: {e}")
                self.status_var.set("❌ Error")
                messagebox.showerror("Error", f"Error: {e}")
            finally:
                self.progress.stop()
        
        threading.Thread(target=run_test, daemon=True).start()
    
    def upload_and_process(self):
        """Upload file and start processing."""
        filename = self.file_var.get()
        if not filename or not Path(filename).exists():
            messagebox.showerror("Error", "Please select a valid audio file")
            return
        
        # Calculate dynamic timeout based on file size
        file_path = Path(filename)
        file_size_mb = file_path.stat().st_size / (1024 * 1024)  # Size in MB
        dynamic_timeout = min(
            BASE_UPLOAD_TIMEOUT + (file_size_mb * UPLOAD_TIMEOUT_PER_MB),
            MAX_UPLOAD_TIMEOUT
        )
        
        # Warn user if file is very large
        if file_size_mb > 50:
            proceed = messagebox.askyesno(
                "Large File Warning",
                f"File size: {file_size_mb:.1f} MB\n"
                f"Estimated upload time: {dynamic_timeout // 60} minutes\n\n"
                f"Large files may take a long time to upload and process.\n"
                f"Continue?"
            )
            if not proceed:
                return
        
        def run_upload():
            self.progress.start()
            self.status_var.set("Uploading file...")
            self.log(f"Uploading file: {filename}")
            self.log(f"File size: {file_size_mb:.2f} MB")
            self.log(f"Upload timeout: {dynamic_timeout // 60} minutes")
            
            try:
                url = self.url_var.get()
                with open(filename, 'rb') as f:
                    files = {'file': (Path(filename).name, f, 'audio/wav')}
                    response = requests.post(
                        f"{url}/api/v1/provenance-check",
                        files=files,
                        timeout=dynamic_timeout,
                        stream=True  # Stream upload for large files
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    self.job_id = data.get('job_id')
                    self.job_id_var.set(self.job_id)
                    self.log(f"✅ Upload successful")
                    self.log(f"Job ID: {self.job_id}")
                    self.status_var.set("✅ Uploaded - Processing...")
                    messagebox.showinfo("Success", f"File uploaded!\nJob ID: {self.job_id}\n\nProcessing started. Check status to monitor progress.")
                    
                    # Auto-check status
                    self.auto_check_status()
                else:
                    self.log(f"❌ Upload failed: {response.status_code}")
                    self.log(f"Response: {response.text}")
                    self.status_var.set("❌ Upload failed")
                    messagebox.showerror("Error", f"Upload failed: {response.status_code}\n{response.text}")
            except requests.exceptions.Timeout:
                self.log(f"❌ Upload timeout after {dynamic_timeout // 60} minutes")
                self.log(f"File size: {file_size_mb:.2f} MB")
                self.status_var.set("❌ Upload Timeout")
                messagebox.showerror("Timeout", 
                    f"Upload timeout after {dynamic_timeout // 60} minutes!\n\n"
                    f"File size: {file_size_mb:.2f} MB\n\n"
                    "Possible solutions:\n"
                    "1. Try a smaller file (< 50 MB recommended)\n"
                    "2. Check network connection speed\n"
                    "3. Verify VPS is running and responsive\n"
                    "4. Check VPS disk space and resources\n\n"
                    "You can also try uploading via command line:\n"
                    f"curl -X POST -F 'file=@{filename}' {url}/api/v1/provenance-check")
            except requests.exceptions.ConnectionError as e:
                self.log(f"❌ Connection error: {e}")
                self.status_var.set("❌ Connection Error")
                messagebox.showerror("Connection Error", f"Cannot connect: {e}")
            except Exception as e:
                self.log(f"❌ Error: {e}")
                self.status_var.set("❌ Error")
                messagebox.showerror("Error", f"Upload error: {e}")
            finally:
                self.progress.stop()
        
        threading.Thread(target=run_upload, daemon=True).start()
    
    def auto_check_status(self):
        """Automatically check status until complete."""
        if not self.job_id:
            return
        
        def check_loop():
            self.log("Waiting for processing to complete...")
            start_time = time.time()
            
            while True:
                try:
                    url = self.url_var.get()
                    response = requests.get(
                        f"{url}/api/v1/status/{self.job_id}",
                        timeout=TIMEOUT
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        status = data.get('status')
                        self.status_var.set(f"Status: {status}")
                        
                        if status == "completed":
                            self.log("✅ Processing completed!")
                            elapsed = time.time() - start_time
                            self.log(f"Processing time: {elapsed:.1f}s")
                            messagebox.showinfo("Success", "Processing completed!\nClick 'Download Report' to view results.")
                            break
                        elif status == "failed":
                            error = data.get('error', 'Unknown error')
                            self.log(f"❌ Processing failed: {error}")
                            self.status_var.set("❌ Processing failed")
                            messagebox.showerror("Error", f"Processing failed:\n{error}")
                            break
                        else:
                            elapsed = time.time() - start_time
                            self.log(f"Status: {status} (elapsed: {elapsed:.1f}s)")
                    
                    time.sleep(2)
                    
                    # Timeout check
                    if time.time() - start_time > MAX_WAIT:
                        self.log(f"⏱️ Timeout after {MAX_WAIT}s")
                        self.status_var.set("⏱️ Timeout")
                        messagebox.showwarning("Timeout", f"Processing timeout after {MAX_WAIT}s")
                        break
                except Exception as e:
                    self.log(f"❌ Status check error: {e}")
                    time.sleep(2)
        
        threading.Thread(target=check_loop, daemon=True).start()
    
    def check_status(self):
        """Check job status."""
        if not self.job_id:
            messagebox.showwarning("Warning", "No job ID. Please upload a file first.")
            return
        
        def run_check():
            self.progress.start()
            self.status_var.set("Checking status...")
            self.log(f"Checking status for job: {self.job_id}")
            
            try:
                url = self.url_var.get()
                response = requests.get(
                    f"{url}/api/v1/status/{self.job_id}",
                    timeout=CONNECT_TIMEOUT
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    self.log(f"Status: {status}")
                    self.status_var.set(f"Status: {status}")
                    
                    if status == "completed":
                        self.log("✅ Processing completed!")
                    elif status == "failed":
                        error = data.get('error', 'Unknown error')
                        self.log(f"❌ Processing failed: {error}")
                    else:
                        self.log(f"⏳ Still processing...")
                    
                    messagebox.showinfo("Status", json.dumps(data, indent=2))
                else:
                    self.log(f"❌ Status check failed: {response.status_code}")
                    self.status_var.set("❌ Status check failed")
                    messagebox.showerror("Error", f"Status check failed: {response.status_code}")
            except Exception as e:
                self.log(f"❌ Error: {e}")
                self.status_var.set("❌ Error")
                messagebox.showerror("Error", f"Status check error: {e}")
            finally:
                self.progress.stop()
        
        threading.Thread(target=run_check, daemon=True).start()
    
    def download_report(self):
        """Download and display report."""
        if not self.job_id:
            messagebox.showwarning("Warning", "No job ID. Please upload a file first.")
            return
        
        def run_download():
            self.progress.start()
            self.status_var.set("Downloading report...")
            self.log(f"Downloading report for job: {self.job_id}")
            
            try:
                url = self.url_var.get()
                response = requests.get(
                    f"{url}/api/v1/reports/{self.job_id}",
                    timeout=TIMEOUT  # Reports can be large
                )
                
                if response.status_code == 200:
                    self.report = response.json()
                    
                    # Save report
                    report_dir = Path("test_reports")
                    report_dir.mkdir(exist_ok=True)
                    report_file = report_dir / f"report_{self.job_id}.json"
                    
                    with open(report_file, 'w') as f:
                        json.dump(self.report, f, indent=2)
                    
                    self.log(f"✅ Report downloaded")
                    self.log(f"Saved to: {report_file}")
                    self.status_var.set("✅ Report downloaded")
                    
                    # Display report summary
                    self.display_report_summary()
                    
                    messagebox.showinfo("Success", f"Report downloaded!\nSaved to: {report_file}")
                else:
                    self.log(f"❌ Download failed: {response.status_code}")
                    self.status_var.set("❌ Download failed")
                    messagebox.showerror("Error", f"Download failed: {response.status_code}")
            except Exception as e:
                self.log(f"❌ Error: {e}")
                self.status_var.set("❌ Error")
                messagebox.showerror("Error", f"Download error: {e}")
            finally:
                self.progress.stop()
        
        threading.Thread(target=run_download, daemon=True).start()
    
    def display_report_summary(self):
        """Display report summary in report text area."""
        if not self.report:
            return
        
        self.report_text.delete(1.0, tk.END)
        
        # Basic info
        self.report_text.insert(tk.END, "=== PROVENANCE REPORT ===\n\n")
        self.report_text.insert(tk.END, f"File ID: {self.report.get('file_id', 'N/A')}\n")
        self.report_text.insert(tk.END, f"Timestamp: {self.report.get('timestamp', 'N/A')}\n\n")
        
        # Summary
        summary = self.report.get('summary', {})
        self.report_text.insert(tk.END, "=== SUMMARY ===\n")
        self.report_text.insert(tk.END, f"Total Segments: {summary.get('total_segments', 0)}\n")
        self.report_text.insert(tk.END, f"Risk Level: {summary.get('risk_level', 'N/A')}\n")
        self.report_text.insert(tk.END, f"AI Probability: {summary.get('ai_probability', 0):.3f}\n")
        self.report_text.insert(tk.END, f"Human Probability: {summary.get('human_probability', 0):.3f}\n\n")
        
        # Segments
        segments = self.report.get('segments', [])
        if segments:
            self.report_text.insert(tk.END, "=== SEGMENTS (First 5) ===\n")
            for i, seg in enumerate(segments[:5], 1):
                self.report_text.insert(tk.END, f"\nSegment {i}:\n")
                self.report_text.insert(tk.END, f"  ID: {seg.get('segment_id', 'N/A')}\n")
                self.report_text.insert(tk.END, f"  Time: {seg.get('start', 0):.2f}s - {seg.get('end', 0):.2f}s\n")
                self.report_text.insert(tk.END, f"  AI Prob: {seg.get('ai_probability', 0):.3f}\n")
                
                matches = seg.get('matches', [])
                if matches:
                    self.report_text.insert(tk.END, f"  Top Match: {matches[0].get('similarity', 0):.3f}\n")
        
        # Model provenance
        model_prov = self.report.get('model_provenance', {})
        self.report_text.insert(tk.END, "\n=== MODEL PROVENANCE ===\n")
        self.report_text.insert(tk.END, f"Model: {model_prov.get('model_name', 'N/A')}\n")
        self.report_text.insert(tk.END, f"Version: {model_prov.get('model_version', 'N/A')}\n")


def main():
    """Run the GUI application."""
    root = tk.Tk()
    app = ProvenanceTestApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

