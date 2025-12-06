"""Step 2: Processing Status component."""
import tkinter as tk
from tkinter import ttk
from typing import Callable
from ..constants import (
    COLOR_BG_DARK, COLOR_BG_CARD, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_ACCENT
)
from ..theme import create_card, create_button


class Step2Processing:
    """Step 2 component: Processing status and job management."""
    
    def __init__(self, parent: tk.Frame,
                 on_check_status: Callable,
                 on_download_report: Callable):
        """
        Initialize Step 2 component.
        
        Args:
            parent: Parent frame
            on_check_status: Callback for check status button
            on_download_report: Callback for download report button
        """
        self.parent = parent
        self.on_check_status = on_check_status
        self.on_download_report = on_download_report
        
        self.frame = None
        self.status_var = tk.StringVar(value="Ready to process")
        self.job_id_var = tk.StringVar()
        self.progress = None
        self.progress_label = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Create Step 2 UI."""
        self.frame = tk.Frame(self.parent, bg=COLOR_BG_DARK)
        step2_card = create_card(self.frame)
        step2_card.pack(fill=tk.BOTH, expand=True)
        
        step2_inner = tk.Frame(step2_card, bg=COLOR_BG_CARD, padx=40, pady=40)
        step2_inner.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            step2_inner,
            text="Processing Status",
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 16, 'bold')
        ).pack(anchor=tk.W, pady=(0, 25))
        
        # Status display
        status_frame = tk.Frame(step2_inner, bg=COLOR_BG_CARD)
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            status_frame,
            textvariable=self.status_var,
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 14)
        ).pack(anchor=tk.W)
        
        # Progress bar
        progress_frame = tk.Frame(step2_inner, bg=COLOR_BG_CARD)
        progress_frame.pack(fill=tk.X, pady=(10, 20))
        
        self.progress = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=600,
            maximum=100
        )
        self.progress.pack(fill=tk.X)
        
        self.progress_label = tk.Label(
            progress_frame,
            text="",
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_SECONDARY,
            font=('Segoe UI', 10)
        )
        self.progress_label.pack(pady=(5, 0))
        
        # Job ID
        job_frame = tk.Frame(step2_inner, bg=COLOR_BG_CARD)
        job_frame.pack(fill=tk.X, pady=(0, 25))
        
        tk.Label(
            job_frame,
            text="Job ID:",
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_SECONDARY,
            font=('Segoe UI', 11)
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        tk.Label(
            job_frame,
            textvariable=self.job_id_var,
            bg=COLOR_BG_CARD,
            fg=COLOR_ACCENT,
            font=('Consolas', 11)
        ).pack(side=tk.LEFT)
        
        # Action buttons
        action_frame = tk.Frame(step2_inner, bg=COLOR_BG_CARD)
        action_frame.pack(fill=tk.X)
        
        check_btn = create_button(action_frame, "Check Status", self.on_check_status, 'secondary')
        check_btn.pack(side=tk.LEFT, padx=(0, 12))
        
        download_btn = create_button(action_frame, "Download Report", self.on_download_report, 'primary')
        download_btn.pack(side=tk.LEFT)
    
    def set_job_id(self, job_id: str):
        """Set job ID."""
        self.job_id_var.set(job_id)
    
    def set_status(self, status: str):
        """Set status text."""
        self.status_var.set(status)
    
    def get_job_id(self) -> str:
        """Get current job ID."""
        return self.job_id_var.get()

