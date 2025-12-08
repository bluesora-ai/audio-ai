"""Step 1: Connection & File Upload component."""
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from typing import Optional, Callable
from ..constants import (
    COLOR_BG_DARK, COLOR_BG_CARD, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_ACCENT, COLOR_BORDER, COLOR_INPUT_BG, COLOR_ERROR, BASE_URL
)
from ..theme import create_card, create_button


class Step1Upload:
    """Step 1 component: API connection and file upload."""
    
    def __init__(self, parent: tk.Frame, url_var: tk.StringVar,
                 on_test_connection: Callable,
                 on_upload: Callable,
                 on_browse_file: Optional[Callable] = None,
                 on_remove_file: Optional[Callable] = None):
        """
        Initialize Step 1 component.
        
        Args:
            parent: Parent frame
            url_var: StringVar for API URL
            on_test_connection: Callback for test connection button
            on_upload: Callback for upload button
            on_browse_file: Optional callback for file browse
            on_remove_file: Optional callback for file removal (called when remove button is clicked)
        """
        self.parent = parent
        self.url_var = url_var
        self.on_test_connection = on_test_connection
        self.on_upload = on_upload
        self.on_browse_file = on_browse_file or self._default_browse_file
        self.on_remove_file = on_remove_file
        
        self.frame = None
        self.file_var = tk.StringVar()
        self.selected_file = None
        self.file_size_mb = 0
        self.upload_progress = None
        self.upload_progress_label = None
        self.file_name_label = None
        self.file_path_entry = None
        self.file_display_container = None
        self.file_info_frame = None
        self.upload_btn = None
        self.drop_frame = None
        self.drop_content = None
        self.browse_enabled = True
        
        self._create_ui()
    
    def _create_ui(self):
        """Create Step 1 UI."""
        self.frame = tk.Frame(self.parent, bg=COLOR_BG_DARK)
        step1_card = create_card(self.frame)
        step1_card.pack(fill=tk.BOTH, expand=True)
        
        step1_inner = tk.Frame(step1_card, bg=COLOR_BG_CARD, padx=40, pady=25)
        step1_inner.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        step1_card.grid_rowconfigure(0, weight=1)
        step1_card.grid_columnconfigure(0, weight=1)
        
        # Configure grid for vertical centering
        for i in range(7):
            step1_inner.grid_rowconfigure(i, weight=1 if i in [0, 6] else 0)
        step1_inner.grid_columnconfigure(0, weight=1)
        
        # Top spacer
        tk.Frame(step1_inner, bg=COLOR_BG_CARD, height=1).grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S)
        )
        
        # API Connection Section
        self._create_api_section(step1_inner)
        
        # Upload Section
        self._create_upload_section(step1_inner)
        
        # File Info Display
        self._create_file_info(step1_inner)
        
        # Progress Bar
        self._create_progress_bar(step1_inner)
        
        # Upload Button
        self.upload_btn = create_button(step1_inner, "Upload & Process Track", self.on_upload, 'primary')
        self.upload_btn.grid(row=5, column=0, sticky=tk.W, pady=(0, 0))
        
        # Bottom spacer
        tk.Frame(step1_inner, bg=COLOR_BG_CARD, height=1).grid(
            row=6, column=0, sticky=(tk.W, tk.E, tk.N, tk.S)
        )
    
    def _create_api_section(self, parent: tk.Frame):
        """Create API connection section."""
        api_section = tk.Frame(parent, bg=COLOR_BG_CARD)
        api_section.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        api_section.grid_columnconfigure(1, weight=1)
        
        tk.Label(
            api_section,
            text="API Connection",
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 16, 'bold')
        ).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 12))
        
        tk.Label(
            api_section,
            text="API URL:",
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_SECONDARY,
            font=('Segoe UI', 11)
        ).grid(row=1, column=0, sticky=tk.W, padx=(0, 12))
        
        url_entry = tk.Entry(
            api_section,
            textvariable=self.url_var,
            font=('Segoe UI', 11),
            bg=COLOR_INPUT_BG,
            fg=COLOR_TEXT_PRIMARY,
            insertbackground=COLOR_TEXT_PRIMARY,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_ACCENT
        )
        url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 12), ipady=10)
        
        test_btn = create_button(api_section, "Test Connection", self.on_test_connection, 'primary')
        test_btn.grid(row=1, column=2, sticky=tk.W)
    
    def _create_upload_section(self, parent: tk.Frame):
        """Create file upload section."""
        upload_section = tk.Frame(parent, bg=COLOR_BG_CARD)
        upload_section.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        upload_section.grid_columnconfigure(0, weight=1)
        
        tk.Label(
            upload_section,
            text="Upload Audio File",
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 16, 'bold')
        ).grid(row=0, column=0, sticky=tk.W, pady=(0, 12))
        
        # Drag and Drop Area
        self.drop_frame = tk.Frame(
            upload_section,
            bg=COLOR_BG_CARD,
            relief=tk.FLAT,
            bd=2,
            highlightthickness=2,
            highlightbackground="#666666",
            highlightcolor="#666666"
        )
        self.drop_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), ipady=10, ipadx=20)
        
        self.drop_content = tk.Frame(self.drop_frame, bg=COLOR_BG_CARD)
        self.drop_content.pack(expand=True, fill=tk.BOTH)
        
        tk.Label(
            self.drop_content,
            text="☁",
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 36)
        ).pack(pady=(12, 8))
        
        tk.Label(
            self.drop_content,
            text="Drag & drop your audio file here",
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 13, 'bold')
        ).pack(pady=(0, 4))
        
        tk.Label(
            self.drop_content,
            text="or click to browse",
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_SECONDARY,
            font=('Segoe UI', 11)
        ).pack()
        
        # Make clickable
        self._bind_browse_handlers()
    
    def _create_file_info(self, parent: tk.Frame):
        """Create file info display."""
        self.file_info_frame = tk.Frame(parent, bg=COLOR_BG_CARD, height=50)
        self.file_info_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        self.file_info_frame.grid_propagate(False)
        self.file_info_frame.grid_columnconfigure(1, weight=1)
        
        self.file_display_container = tk.Frame(self.file_info_frame, bg=COLOR_BG_CARD)
        self.file_display_container.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=0, pady=5)
        self.file_display_container.grid_columnconfigure(1, weight=1)
        self.file_display_container.grid_remove()
        
        self.file_name_label = tk.Label(
            self.file_display_container,
            text="",
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 11),
            anchor=tk.W
        )
        self.file_name_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 15))
        
        self.file_path_entry = tk.Entry(
            self.file_display_container,
            textvariable=self.file_var,
            font=('Segoe UI', 10),
            bg=COLOR_INPUT_BG,
            fg=COLOR_TEXT_SECONDARY,
            insertbackground=COLOR_TEXT_PRIMARY,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_ACCENT,
            readonlybackground=COLOR_INPUT_BG,
            state='readonly',
            width=30
        )
        self.file_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10), ipady=6)
        
        remove_btn = tk.Button(
            self.file_display_container,
            text="×",
            command=self.remove_file,
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_SECONDARY,
            font=('Segoe UI', 14, 'bold'),
            relief=tk.FLAT,
            padx=8,
            pady=2,
            cursor='hand2',
            activebackground=COLOR_ERROR,
            activeforeground=COLOR_TEXT_PRIMARY,
            bd=0,
            highlightthickness=0
        )
        remove_btn.grid(row=0, column=2, sticky=tk.E)
    
    def _create_progress_bar(self, parent: tk.Frame):
        """Create upload progress bar."""
        upload_progress_frame = tk.Frame(parent, bg=COLOR_BG_CARD)
        upload_progress_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        upload_progress_frame.grid_columnconfigure(0, weight=1)
        
        self.upload_progress = ttk.Progressbar(
            upload_progress_frame,
            mode='determinate',
            maximum=100
        )
        self.upload_progress.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.upload_progress_label = tk.Label(
            upload_progress_frame,
            text="",
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_SECONDARY,
            font=('Segoe UI', 9)
        )
        self.upload_progress_label.grid(row=1, column=0, sticky=tk.W)
    
    def _on_browse_click(self, event):
        """Handle browse click event."""
        if self.browse_enabled:
            self.on_browse_file()
    
    def _on_browse_enter(self, event):
        """Handle browse enter event."""
        if self.browse_enabled and self.drop_frame:
            self.drop_frame.config(highlightbackground=COLOR_ACCENT, cursor='hand2')
    
    def _on_browse_leave(self, event):
        """Handle browse leave event."""
        if self.drop_frame:
            self.drop_frame.config(highlightbackground="#666666", cursor='')
    
    def _bind_browse_handlers(self):
        """Bind click handlers for browse functionality."""
        if self.drop_frame and self.drop_content:
            for widget in [self.drop_frame, self.drop_content]:
                widget.bind("<Button-1>", self._on_browse_click)
                widget.bind("<Enter>", self._on_browse_enter)
                widget.bind("<Leave>", self._on_browse_leave)
    
    def _unbind_browse_handlers(self):
        """Unbind click handlers for browse functionality."""
        if self.drop_frame and self.drop_content:
            for widget in [self.drop_frame, self.drop_content]:
                widget.unbind("<Button-1>")
                widget.unbind("<Enter>")
                widget.unbind("<Leave>")
    
    def _default_browse_file(self):
        """Default file browse handler."""
        if not self.browse_enabled:
            return
        filename = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.flac *.m4a *.aac"),
                ("WAV files", "*.wav"),
                ("MP3 files", "*.mp3"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.set_file(filename)
    
    def set_file(self, filename: str):
        """Set selected file and update UI."""
        self.selected_file = filename
        self.file_var.set(filename)
        self.file_size_mb = Path(filename).stat().st_size / (1024 * 1024)
        
        file_name = Path(filename).name
        display_name = f"{file_name} ({self.file_size_mb:.1f} MB)"
        
        self.file_name_label.config(text=display_name)
        self.file_display_container.grid()
    
    def remove_file(self):
        """Remove selected file."""
        # Call the callback if provided (e.g., to cancel upload)
        if self.on_remove_file:
            self.on_remove_file()
        
        self.selected_file = None
        self.file_var.set("")
        self.file_size_mb = 0
        self.file_display_container.grid_remove()
        self.upload_progress.config(value=0)
        self.upload_progress_label.config(text="")
    
    def get_selected_file(self) -> Optional[str]:
        """Get selected file path."""
        return self.selected_file or self.file_var.get()
    
    def get_file_size_mb(self) -> float:
        """Get selected file size in MB."""
        return self.file_size_mb
    
    def set_upload_enabled(self, enabled: bool):
        """Enable or disable the upload button."""
        if self.upload_btn:
            if enabled:
                self.upload_btn.config(state=tk.NORMAL, cursor='hand2')
            else:
                self.upload_btn.config(state=tk.DISABLED, cursor='arrow')
    
    def set_browse_enabled(self, enabled: bool):
        """Enable or disable the browse file functionality."""
        self.browse_enabled = enabled
        if enabled:
            self._bind_browse_handlers()
            if self.drop_frame:
                self.drop_frame.config(highlightbackground="#666666", cursor='hand2')
            if self.drop_content:
                self.drop_content.config(cursor='hand2')
        else:
            self._unbind_browse_handlers()
            if self.drop_frame:
                self.drop_frame.config(highlightbackground="#333333", cursor='arrow')
            if self.drop_content:
                self.drop_content.config(cursor='arrow')

