"""Main application orchestrator for Beatlibrary Audio Provenance GUI."""
import tkinter as tk
import threading
import json
import time
from pathlib import Path
from typing import Optional, Dict

from .constants import (
    COLOR_BG_DARK, COLOR_BG_CARD, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_ACCENT, COLOR_ACCENT_HOVER, BASE_URL, MAX_WAIT,
    BASE_UPLOAD_TIMEOUT, UPLOAD_TIMEOUT_PER_MB, MAX_UPLOAD_TIMEOUT,
    WINDOW_TITLE, WINDOW_SIZE, WINDOW_MIN_SIZE, STEP_NAMES
)
from .dialogs import CustomAlert, CustomConfirm
from .theme import setup_dark_theme, create_button
from .api_client import APIClient
from .utils import Logger, apply_dark_title_bar, set_window_icon
from .report_display import ReportDisplayer
from .visualizations import ChartGenerator, HAS_MATPLOTLIB
from .steps import Step1Upload, Step2Processing, Step3Report


class BeatlibraryProvenanceApp:
    """Modern dark-themed desktop interface for Beatlibrary Audio Provenance API."""
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the main application.
        
        Args:
            root: Root Tkinter window
        """
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(*WINDOW_MIN_SIZE)
        self.root.configure(bg=COLOR_BG_DARK)
        
        # Set icon
        self.icon_path = set_window_icon(root)
        
        # Configure root grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Setup theme
        setup_dark_theme()
        
        # State
        self.job_id: Optional[str] = None
        self.report: Optional[Dict] = None
        self.viz_generated = False
        self.current_step = 1
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.upload_cancelled = False
        self.upload_in_progress = False
        
        # API client
        self.url_var = tk.StringVar(value=BASE_URL)
        self.api_client = APIClient(BASE_URL)
        
        # Components
        self.step1 = None
        self.step2 = None
        self.step3 = None
        self.logger = None
        self.report_displayer = None
        self.chart_generator = None
        
        # UI elements
        self.step_container = None
        self.progress_circles = []
        self.progress_texts = []
        self.prev_btn = None
        self.next_btn = None
        
        # Setup UI
        self._setup_ui()
        
        # Apply dark title bar after window is shown
        self.root.after(100, lambda: apply_dark_title_bar(self.root))
        
        # Re-apply icon
        if self.icon_path:
            self.root.after(300, lambda: set_window_icon(self.root, self.icon_path))
    
    def _setup_ui(self):
        """Setup wizard-style step-by-step interface."""
        main_container = tk.Frame(self.root, bg=COLOR_BG_DARK)
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=40, pady=30)
        
        main_container.grid_rowconfigure(2, weight=1)
        main_container.grid_rowconfigure(3, weight=0)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Header
        self._create_header(main_container)
        
        # Step container
        self.step_container = tk.Frame(main_container, bg=COLOR_BG_DARK)
        self.step_container.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create steps
        self._create_steps()
        
        # Navigation buttons
        self._create_navigation(main_container)
        
        # Initialize to step 1
        self.show_step(1)
    
    def _create_header(self, parent: tk.Frame):
        """Create header with title and progress indicator."""
        header_frame = tk.Frame(parent, bg=COLOR_BG_DARK)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 30))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)
        
        # Make draggable
        def start_drag(event):
            self.drag_start_x = event.x_root - self.root.winfo_x()
            self.drag_start_y = event.y_root - self.root.winfo_y()
        
        def on_drag(event):
            x = event.x_root - self.drag_start_x
            y = event.y_root - self.drag_start_y
            self.root.geometry(f"+{x}+{y}")
        
        header_frame.bind("<Button-1>", start_drag)
        header_frame.bind("<B1-Motion>", on_drag)
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="Provenance Report",
            bg=COLOR_BG_DARK,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 24, 'bold'),
            anchor=tk.W
        )
        title_label.grid(row=0, column=0, sticky=tk.W)
        title_label.bind("<Button-1>", start_drag)
        title_label.bind("<B1-Motion>", on_drag)
        
        # Progress indicator
        progress_frame = tk.Frame(header_frame, bg=COLOR_BG_DARK)
        progress_frame.grid(row=0, column=1, sticky=tk.E)
        
        for i in range(1, 4):
            step_container = tk.Frame(progress_frame, bg=COLOR_BG_DARK)
            step_container.pack(side=tk.LEFT)
            
            circle_canvas = tk.Canvas(
                step_container,
                width=24,
                height=24,
                bg=COLOR_BG_DARK,
                highlightthickness=0
            )
            circle_canvas.pack(side=tk.LEFT, padx=(0, 8))
            
            circle_id = circle_canvas.create_oval(2, 2, 22, 22, fill=COLOR_BG_CARD, outline="", width=0)
            text_id = circle_canvas.create_text(12, 12, text=str(i), fill=COLOR_TEXT_SECONDARY,
                                               font=('Segoe UI', 11, 'bold'))
            
            self.progress_circles.append({
                'canvas': circle_canvas,
                'circle': circle_id,
                'text': text_id
            })
            
            step_name_label = tk.Label(
                step_container,
                text=STEP_NAMES[i-1],
                bg=COLOR_BG_DARK,
                fg=COLOR_TEXT_SECONDARY,
                font=('Segoe UI', 10)
            )
            step_name_label.pack(side=tk.LEFT)
            self.progress_texts.append(step_name_label)
            
            if i < 3:
                separator = tk.Frame(progress_frame, bg=COLOR_ACCENT, width=2, height=1)
                separator.pack(side=tk.LEFT, padx=15, fill=tk.Y, ipady=2)
    
    def _create_steps(self):
        """Create all step components."""
        # Step 1: Upload
        self.step1 = Step1Upload(
            self.step_container,
            self.url_var,
            self.test_health,
            self.upload_and_process,
            on_remove_file=self.handle_remove_file
        )
        
        # Step 2: Processing
        self.step2 = Step2Processing(
            self.step_container,
            self.check_status,
            self.download_report
        )
        
        # Step 3: Report
        self.step3 = Step3Report(self.step_container)
        
        # Setup logger
        self.logger = Logger(self.step3.log_text, self.root)
        
        # Setup report displayer
        self.report_displayer = ReportDisplayer(
            self.step3.summary_text_left,
            self.step3.summary_text_right,
            self.step3.details_text
        )
        
        # Setup chart generator
        self.chart_generator = ChartGenerator(
            self.step3.viz_container,
            self.step3.viz_canvas,
            self.step3.viz_canvas_window_id
        )
        
        # Bind tab change for lazy loading
        self.step3.bind_tab_change(self._on_tab_changed)
    
    def _create_navigation(self, parent: tk.Frame):
        """Create navigation buttons."""
        nav_frame = tk.Frame(parent, bg=COLOR_BG_DARK, height=60)
        nav_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(20, 0))
        nav_frame.grid_propagate(False)
        nav_frame.columnconfigure(0, weight=1)
        
        btn_container = tk.Frame(nav_frame, bg=COLOR_BG_DARK)
        btn_container.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.prev_btn = create_button(btn_container, "← Previous", self.previous_step, 'secondary')
        self.prev_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.next_btn = create_button(btn_container, "Next →", self.next_step, 'primary')
        self.next_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        nav_frame.lift()
    
    def show_step(self, step_num: int):
        """Show the specified step and hide others."""
        self.current_step = step_num
        
        # Hide all steps
        for step in [self.step1, self.step2, self.step3]:
            if step and step.frame:
                step.frame.pack_forget()
        
        # Show current step
        if step_num == 1 and self.step1:
            self.step1.frame.pack(fill=tk.BOTH, expand=True)
        elif step_num == 2 and self.step2:
            self.step2.frame.pack(fill=tk.BOTH, expand=True)
        elif step_num == 3 and self.step3:
            self.step3.frame.pack(fill=tk.BOTH, expand=True)
        
        self.root.update_idletasks()
        
        # Update progress indicators
        self._update_progress_indicators(step_num)
        
        # Update navigation buttons
        self._update_navigation_buttons()
    
    def _update_progress_indicators(self, step_num: int):
        """Update progress indicator circles and text."""
        for i in range(1, 4):
            circle_idx = i - 1
            if circle_idx < len(self.progress_circles) and circle_idx < len(self.progress_texts):
                circle_data = self.progress_circles[circle_idx]
                text_label = self.progress_texts[circle_idx]
                
                if i < step_num:
                    circle_data['canvas'].itemconfig(circle_data['circle'], fill=COLOR_BG_CARD)
                    circle_data['canvas'].itemconfig(circle_data['text'], fill=COLOR_TEXT_SECONDARY)
                    text_label.config(fg=COLOR_TEXT_SECONDARY)
                elif i == step_num:
                    circle_data['canvas'].itemconfig(circle_data['circle'], fill=COLOR_ACCENT)
                    circle_data['canvas'].itemconfig(circle_data['text'], fill=COLOR_TEXT_PRIMARY)
                    text_label.config(fg=COLOR_ACCENT_HOVER)
                else:
                    circle_data['canvas'].itemconfig(circle_data['circle'], fill=COLOR_BG_CARD)
                    circle_data['canvas'].itemconfig(circle_data['text'], fill=COLOR_TEXT_SECONDARY)
                    text_label.config(fg=COLOR_TEXT_SECONDARY)
    
    def _update_navigation_buttons(self):
        """Update navigation button states."""
        # Previous button
        if self.current_step > 1:
            self.prev_btn.config(state=tk.NORMAL, cursor='hand2',
                               bg=COLOR_BG_CARD, fg=COLOR_TEXT_PRIMARY,
                               activebackground=COLOR_BG_CARD)
        else:
            self.prev_btn.config(state=tk.DISABLED, cursor='arrow',
                               bg=COLOR_BG_CARD, fg=COLOR_TEXT_SECONDARY)
        
        # Next button
        if self.current_step == 1:
            step1_complete = self.job_id is not None
            if step1_complete:
                self.next_btn.config(state=tk.NORMAL, text="Next →",
                                   cursor='hand2', bg=COLOR_ACCENT, fg=COLOR_TEXT_PRIMARY)
            else:
                self.next_btn.config(state=tk.DISABLED, text="Next → (Upload file first)",
                                   cursor='arrow', bg=COLOR_BG_CARD, fg=COLOR_TEXT_SECONDARY)
        elif self.current_step == 2:
            step2_complete = self.report is not None
            if step2_complete:
                self.next_btn.config(state=tk.NORMAL, text="Next →",
                                   cursor='hand2', bg=COLOR_ACCENT, fg=COLOR_TEXT_PRIMARY)
            else:
                self.next_btn.config(state=tk.DISABLED, text="Next → (Download report first)",
                                   cursor='arrow', bg=COLOR_BG_CARD, fg=COLOR_TEXT_SECONDARY)
        else:
            self.next_btn.config(state=tk.DISABLED, text="Complete",
                               cursor='arrow', bg=COLOR_BG_CARD, fg=COLOR_TEXT_SECONDARY)
    
    def next_step(self):
        """Navigate to next step."""
        if self.current_step == 1 and not self.job_id:
            self.show_alert("Step Not Complete", "Please upload an audio file first.", 'warning')
            return
        elif self.current_step == 2 and not self.report:
            self.show_alert("Step Not Complete", "Please download the report first.", 'warning')
            return
        
        if self.current_step < 3:
            self.show_step(self.current_step + 1)
    
    def previous_step(self):
        """Navigate to previous step."""
        if self.current_step > 1:
            self.show_step(self.current_step - 1)
    
    def show_alert(self, title: str, message: str, alert_type: str = 'info'):
        """Show custom alert dialog."""
        alert = CustomAlert(self.root, title, message, alert_type)
        alert.show()
    
    def show_confirm(self, title: str, message: str) -> bool:
        """Show custom confirmation dialog."""
        confirm = CustomConfirm(self.root, title, message)
        return confirm.show()
    
    def test_health(self):
        """Test API health endpoint."""
        def run_test():
            self.root.after(0, lambda: self.step2.progress.config(mode='indeterminate'))
            self.root.after(0, lambda: self.step2.progress.start())
            self.root.after(0, lambda: self.step2.progress_label.config(text="Testing connection..."))
            self.root.after(0, lambda: self.step2.set_status("Testing connection..."))
            self.logger.log("Testing API health endpoint...", "INFO")
            
            try:
                self.api_client.base_url = self.url_var.get().rstrip('/')
                data = self.api_client.test_health()
                self.logger.log(f"✅ Connection successful: {data}", "SUCCESS")
                self.step2.set_status("✅ Connected")
                self.show_alert("Success", f"Connection successful!\n\n{json.dumps(data, indent=2)}", 'success')
            except Exception as e:
                self.logger.log(f"❌ Connection error: {e}", "ERROR")
                self.step2.set_status("❌ Connection Error")
                self.show_alert("Error", f"Cannot connect to API!\n\n{e}", 'error')
            finally:
                self.root.after(0, lambda: self.step2.progress.stop())
                self.root.after(0, lambda: self.step2.progress_label.config(text=""))
        
        threading.Thread(target=run_test, daemon=True).start()
    
    def handle_remove_file(self):
        """Handle file removal - cancel upload if in progress."""
        if self.upload_in_progress:
            self.upload_cancelled = True
            self.logger.log("Upload cancellation requested...", "INFO")
            self.step2.set_status("Cancelling upload...")
            # Immediately re-enable upload button and browse functionality
            self.step1.set_upload_enabled(True)
            self.step1.set_browse_enabled(True)
    
    def upload_and_process(self):
        """Upload file and start processing."""
        filename = self.step1.get_selected_file()
        if not filename or not Path(filename).exists():
            self.show_alert("Error", "Please select a valid audio file", 'error')
            return
        
        file_path = Path(filename)
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        dynamic_timeout = min(
            BASE_UPLOAD_TIMEOUT + (file_size_mb * UPLOAD_TIMEOUT_PER_MB),
            MAX_UPLOAD_TIMEOUT
        )
        
        # Disable upload button and browse functionality when upload starts
        self.step1.set_upload_enabled(False)
        self.step1.set_browse_enabled(False)
        
        # Reset cancellation flag and set upload in progress
        self.upload_cancelled = False
        self.upload_in_progress = True
        
        def run_upload():
            self.root.after(0, lambda: self.step1.upload_progress.config(mode='determinate', maximum=100, value=0))
            self.root.after(0, lambda: self.step1.upload_progress_label.config(text="0% - Starting upload..."))
            self.root.after(0, lambda: self.step2.progress.config(mode='determinate', maximum=100, value=0))
            self.root.after(0, lambda: self.step2.progress_label.config(text="0%"))
            self.root.after(0, lambda: self.step2.set_status("Uploading track..."))
            self.logger.log(f"Uploading: {file_path.name}", "INFO")
            
            def cancellation_check():
                """Check if upload should be cancelled."""
                return self.upload_cancelled
            
            def progress_callback(uploaded, total):
                # Check if upload was cancelled
                if self.upload_cancelled:
                    return
                
                if total > 0:
                    percent = min(int((uploaded / total) * 100), 100)
                    self.root.after(0, lambda p=percent: self.step1.upload_progress.config(value=p))
                    self.root.after(0, lambda p=percent, u=uploaded, t=total:
                        self.step1.upload_progress_label.config(
                            text=f"{p}% ({u / (1024*1024):.2f} MB / {t / (1024*1024):.2f} MB)"
                        ))
                    self.root.after(0, lambda p=percent: self.step2.progress.config(value=p))
                    self.root.after(0, lambda p=percent, u=uploaded, t=total:
                        self.step2.progress_label.config(
                            text=f"{p}% ({u / (1024*1024):.2f} MB / {t / (1024*1024):.2f} MB)"
                        ))
            
            try:
                # Check if cancelled before starting upload
                if self.upload_cancelled:
                    self.logger.log("Upload cancelled by user", "INFO")
                    self.root.after(0, lambda: self.step2.set_status("Upload cancelled"))
                    return
                
                self.api_client.base_url = self.url_var.get().rstrip('/')
                response = self.api_client.upload_file(file_path, progress_callback, cancellation_check)
                
                # Check if cancelled after upload completes
                if self.upload_cancelled:
                    self.logger.log("Upload cancelled by user", "INFO")
                    self.root.after(0, lambda: self.step2.set_status("Upload cancelled"))
                    self.root.after(0, lambda: self.step1.upload_progress_label.config(text="Cancelled"))
                    self.root.after(0, lambda: self.step2.progress_label.config(text="Cancelled"))
                    return
                
                self.job_id = response.get('job_id')
                self.step2.set_job_id(self.job_id)
                self.logger.log(f"✅ Upload successful", "SUCCESS")
                self.logger.log(f"Job ID: {self.job_id}", "INFO")
                self.step2.set_status("✅ Uploaded - Processing...")
                
                self.show_alert(
                    "Success",
                    f"Track uploaded successfully!\n\nJob ID: {self.job_id}\n\n"
                    f"Processing has started. Click 'Next' to monitor progress.",
                    'success'
                )
                
                self.root.after(0, lambda: self.show_step(2))
                self.root.after(0, lambda: self.auto_check_status())
            except Exception as e:
                # Check if it's a cancellation exception
                from gui.api_client import UploadCancelledException
                if isinstance(e, UploadCancelledException) or self.upload_cancelled:
                    self.logger.log("Upload cancelled by user", "INFO")
                    self.root.after(0, lambda: self.step2.set_status("Upload cancelled"))
                else:
                    self.logger.log(f"❌ Upload error: {e}", "ERROR")
                    self.step2.set_status("❌ Upload Error")
                    self.show_alert("Error", f"Upload error: {e}", 'error')
            finally:
                self.upload_in_progress = False
                # Re-enable upload button and browse functionality when upload finishes (success or error)
                self.root.after(0, lambda: self.step1.set_upload_enabled(True))
                self.root.after(0, lambda: self.step1.set_browse_enabled(True))
                if not self.upload_cancelled:
                    self.root.after(2000, lambda: self.step1.upload_progress_label.config(text=""))
                    self.root.after(2000, lambda: self.step2.progress_label.config(text=""))
        
        threading.Thread(target=run_upload, daemon=True).start()
    
    def auto_check_status(self):
        """Automatically check status until complete."""
        if not self.job_id:
            return
        
        def check_loop():
            self.logger.log("Waiting for processing to complete...", "INFO")
            start_time = time.time()
            
            while True:
                try:
                    self.api_client.base_url = self.url_var.get().rstrip('/')
                    status_data = self.api_client.get_status(self.job_id)
                    status = status_data.get('status')
                    self.step2.set_status(f"Status: {status.title()}")
                    
                    if status == "completed":
                        self.logger.log("✅ Processing completed!", "SUCCESS")
                        self.step2.set_status("✅ Processing Complete")
                        # Notification removed - only show notification after upload, not after processing
                        break
                    elif status == "failed":
                        error = status_data.get('error', 'Unknown error')
                        self.logger.log(f"❌ Processing failed: {error}", "ERROR")
                        self.step2.set_status("❌ Processing failed")
                        self.show_alert("Error", f"Processing failed:\n{error}", 'error')
                        break
                    
                    if time.time() - start_time > MAX_WAIT:
                        self.logger.log(f"⏱️ Timeout after {MAX_WAIT}s", "WARNING")
                        self.step2.set_status("⏱️ Timeout")
                        break
                    
                    sleep_time = 2 if status == "processing" else 5
                    time.sleep(sleep_time)
                except Exception as e:
                    self.logger.log(f"❌ Status check error: {e}", "ERROR")
                    time.sleep(2)
        
        threading.Thread(target=check_loop, daemon=True).start()
    
    def check_status(self):
        """Check job status manually."""
        if not self.job_id:
            self.show_alert("Warning", "No job ID. Please upload a file first.", 'warning')
            return
        
        def run_check():
            self.root.after(0, lambda: self.step2.progress.config(mode='indeterminate'))
            self.root.after(0, lambda: self.step2.progress.start())
            self.root.after(0, lambda: self.step2.progress_label.config(text="Checking status..."))
            self.logger.log(f"Checking status for job: {self.job_id}", "INFO")
            
            try:
                self.api_client.base_url = self.url_var.get().rstrip('/')
                status_data = self.api_client.get_status(self.job_id)
                status = status_data.get('status')
                self.step2.set_status(f"Status: {status.title()}")
                self.show_alert("Status", json.dumps(status_data, indent=2), 'info')
            except Exception as e:
                self.logger.log(f"❌ Error: {e}", "ERROR")
                self.show_alert("Error", f"Status check error: {e}", 'error')
            finally:
                self.root.after(0, lambda: self.step2.progress.stop())
                self.root.after(0, lambda: self.step2.progress_label.config(text=""))
        
        threading.Thread(target=run_check, daemon=True).start()
    
    def download_report(self):
        """Download and display report."""
        if not self.job_id:
            self.show_alert("Warning", "No job ID. Please upload a file first.", 'warning')
            return
        
        def run_download():
            self.root.after(0, lambda: self.step2.progress.config(mode='indeterminate'))
            self.root.after(0, lambda: self.step2.progress.start())
            self.root.after(0, lambda: self.step2.progress_label.config(text="Downloading report..."))
            self.logger.log(f"Downloading report for job: {self.job_id}", "INFO")
            
            try:
                self.api_client.base_url = self.url_var.get().rstrip('/')
                self.report = self.api_client.get_report(self.job_id)
                
                # Save report
                report_dir = Path("test_reports")
                report_dir.mkdir(exist_ok=True)
                report_file = report_dir / f"report_{self.job_id}.json"
                
                with open(report_file, 'w') as f:
                    json.dump(self.report, f, indent=2)
                
                self.logger.log(f"✅ Report downloaded", "SUCCESS")
                self.logger.log(f"Saved to: {report_file}", "INFO")
                self.step2.set_status("✅ Report downloaded")
                
                # Display reports
                self.report_displayer.display_summary(self.report)
                self.report_displayer.display_full_report(self.report)
                
                # Mark visualizations as not generated
                self.viz_generated = False
                if not HAS_MATPLOTLIB:
                    self.logger.log("⚠️ Matplotlib not available. Visualizations disabled.", "WARNING")
                
                if self.current_step == 2:
                    self.root.after(0, lambda: self.show_step(2))
                
                self.show_alert("Success", f"Report downloaded successfully!\n\nSaved to: {report_file}", 'success')
            except Exception as e:
                self.logger.log(f"❌ Error: {e}", "ERROR")
                self.show_alert("Error", f"Download error: {e}", 'error')
            finally:
                self.root.after(0, lambda: self.step2.progress.stop())
                self.root.after(0, lambda: self.step2.progress_label.config(text=""))
        
        threading.Thread(target=run_download, daemon=True).start()
    
    def _on_tab_changed(self, tab_name: str):
        """Handle tab change event for lazy loading."""
        if 'Visualizations' in tab_name and self.report and not self.viz_generated:
            self._generate_visualizations()
    
    def _generate_visualizations(self):
        """Generate visualizations for the report."""
        if not self.report or not HAS_MATPLOTLIB:
            return
        
        def generate():
            segments = self.report.get('segments', [])
            overall = self.report.get('overall_summary', {})
            
            if not segments:
                return
            
            # Extract data
            segment_times = []
            ai_probs = []
            fusion_scores = []
            risk_flags = []
            stem_types = []
            
            for seg in segments:
                start = seg.get('start', 0)
                end = seg.get('end', 0)
                segment_times.append((start + end) / 2)
                
                stems = seg.get('stems', [])
                if stems:
                    stem = stems[0]
                    classifier = stem.get('classifier', {})
                    ai_probs.append(classifier.get('ai_probability', 0.0))
                    fusion_scores.append(stem.get('fusion_score', 0.0))
                    risk_flags.append(seg.get('risk_flag', 'low'))
                    stem_types.append(stem.get('stem_type', 'unknown'))
                else:
                    ai_probs.append(seg.get('ai_probability', 0.0))
                    fusion_scores.append(0.0)
                    risk_flags.append(seg.get('risk_flag', 'low'))
                    stem_types.append('unknown')
            
            # Clear container
            self.root.after(0, lambda: [w.destroy() for w in self.step3.viz_container.winfo_children()])
            
            # Configure grid
            def create_charts():
                for w in self.step3.viz_container.winfo_children():
                    w.destroy()
                
                self.step3.viz_container.grid_rowconfigure(0, weight=1)
                self.step3.viz_container.grid_rowconfigure(1, weight=1)
                self.step3.viz_container.grid_columnconfigure(0, weight=1)
                self.step3.viz_container.grid_columnconfigure(1, weight=1)
                
                # Generate charts
                self.chart_generator.create_timeline_chart(
                    segment_times, ai_probs, fusion_scores,
                    "AI Probability & Fusion Score Timeline",
                    "Time (seconds)", "Probability",
                    grid_pos=(0, 0)
                )
                
                self.chart_generator.create_risk_distribution_chart(risk_flags, grid_pos=(0, 1))
                self.chart_generator.create_stems_analysis_chart(stem_types, ai_probs, grid_pos=(1, 0))
                self.chart_generator.create_summary_pie_chart(
                    overall.get('overall_ai_probability', 0.0), grid_pos=(1, 1)
                )
                
                self.step3.viz_container.update_idletasks()
                self.step3.viz_canvas.configure(scrollregion=self.step3.viz_canvas.bbox("all"))
            
            self.root.after(0, create_charts)
            self.viz_generated = True
        
        threading.Thread(target=generate, daemon=True).start()


def main():
    """Run the Beatlibrary Provenance application."""
    root = tk.Tk()
    app = BeatlibraryProvenanceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

