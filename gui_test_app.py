"""Beatlibrary Audio Provenance API - Modern Dark UI."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
import json
import threading
import time
from pathlib import Path
from typing import Optional, Dict
import numpy as np

# Matplotlib for visualizations
HAS_MATPLOTLIB = False
try:
    import matplotlib
    # Set backend before importing pyplot
    matplotlib.use('TkAgg', force=False)  # Use Tkinter backend
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError as e:
    print(f"Warning: matplotlib not available. Visualizations will be disabled.")
    print(f"ImportError details: {e}")
except Exception as e:
    print(f"Warning: matplotlib initialization failed. Visualizations will be disabled.")
    print(f"Error details: {e}")

# Configuration
VPS_IP = "78.46.37.169"
BASE_URL = f"http://{VPS_IP}:8000"
TIMEOUT = 600
CONNECT_TIMEOUT = 30
MAX_WAIT = 1800

# Timeout calculation
BASE_UPLOAD_TIMEOUT = 300
UPLOAD_TIMEOUT_PER_MB = 30
MAX_UPLOAD_TIMEOUT = 1800

# Modern Dark Theme Colors
COLOR_BG_DARK = "#000000"  # Pure black background
COLOR_BG_CARD = "#1A1A1A"  # Dark card background
COLOR_BG_HOVER = "#2A2A2A"  # Hover state
COLOR_TEXT_PRIMARY = "#FFFFFF"  # White text
COLOR_TEXT_SECONDARY = "#B0B0B0"  # Gray text
COLOR_ACCENT = "#6366F1"  # Indigo accent
COLOR_ACCENT_HOVER = "#818CF8"  # Lighter indigo
COLOR_SUCCESS = "#10B981"  # Green
COLOR_WARNING = "#F59E0B"  # Amber
COLOR_ERROR = "#EF4444"  # Red
COLOR_BORDER = "#333333"  # Dark border
COLOR_INPUT_BG = "#0F0F0F"  # Input background


class CustomAlert:
    """Custom dark-themed alert dialog matching the app design."""
    
    def __init__(self, parent, title, message, alert_type='info'):
        self.parent = parent
        self.result = None
        
        # Create top-level window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("450x200")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=COLOR_BG_DARK)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog on parent window
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (450 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (200 // 2)
        self.dialog.geometry(f"450x200+{x}+{y}")
        
        # Remove default window decorations for custom look
        self.dialog.overrideredirect(False)
        
        # Set icon
        try:
            if hasattr(parent, 'icon_path'):
                self.dialog.iconbitmap(parent.icon_path)
        except:
            pass
        
        # Main container
        container = tk.Frame(self.dialog, bg=COLOR_BG_DARK)
        container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Title bar
        title_frame = tk.Frame(container, bg=COLOR_BG_CARD, height=50)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)
        
        # Icon and title
        icon_text = "✓" if alert_type == 'success' else "⚠" if alert_type == 'warning' else "✕" if alert_type == 'error' else "ℹ"
        icon_color = COLOR_SUCCESS if alert_type == 'success' else COLOR_WARNING if alert_type == 'warning' else COLOR_ERROR if alert_type == 'error' else COLOR_ACCENT
        
        icon_label = tk.Label(
            title_frame,
            text=icon_text,
            bg=COLOR_BG_CARD,
            fg=icon_color,
            font=('Segoe UI', 20, 'bold')
        )
        icon_label.pack(side=tk.LEFT, padx=(20, 12))
        
        title_label = tk.Label(
            title_frame,
            text=title,
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 14, 'bold')
        )
        title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Close button
        close_btn = tk.Button(
            title_frame,
            text="×",
            command=self.dialog.destroy,
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_SECONDARY,
            font=('Segoe UI', 18, 'bold'),
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=0,
            cursor='hand2',
            activebackground=COLOR_ERROR,
            activeforeground=COLOR_TEXT_PRIMARY
        )
        close_btn.pack(side=tk.RIGHT)
        
        # Content area
        content_frame = tk.Frame(container, bg=COLOR_BG_DARK)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # Message text
        message_label = tk.Label(
            content_frame,
            text=message,
            bg=COLOR_BG_DARK,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 11),
            justify=tk.LEFT,
            wraplength=400
        )
        message_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Button frame
        btn_frame = tk.Frame(content_frame, bg=COLOR_BG_DARK)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # OK button
        ok_btn = tk.Button(
            btn_frame,
            text="OK",
            command=self.dialog.destroy,
            bg=COLOR_ACCENT,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            bd=0,
            padx=30,
            pady=10,
            cursor='hand2',
            activebackground=COLOR_ACCENT_HOVER,
            activeforeground=COLOR_TEXT_PRIMARY
        )
        ok_btn.pack(side=tk.RIGHT)
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.dialog.destroy())
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
        # Focus on dialog
        self.dialog.focus_set()
        ok_btn.focus_set()
    
    def show(self):
        """Show the dialog and wait for user response."""
        self.dialog.wait_window()
        return self.result


class CustomConfirm:
    """Custom dark-themed confirmation dialog."""
    
    def __init__(self, parent, title, message):
        self.parent = parent
        self.result = False
        
        # Create top-level window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("450x200")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=COLOR_BG_DARK)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (450 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (200 // 2)
        self.dialog.geometry(f"450x200+{x}+{y}")
        
        # Main container
        container = tk.Frame(self.dialog, bg=COLOR_BG_DARK)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Title bar
        title_frame = tk.Frame(container, bg=COLOR_BG_CARD, height=50)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)
        
        icon_label = tk.Label(
            title_frame,
            text="⚠",
            bg=COLOR_BG_CARD,
            fg=COLOR_WARNING,
            font=('Segoe UI', 20, 'bold')
        )
        icon_label.pack(side=tk.LEFT, padx=(20, 12))
        
        title_label = tk.Label(
            title_frame,
            text=title,
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 14, 'bold')
        )
        title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        close_btn = tk.Button(
            title_frame,
            text="×",
            command=self.dialog.destroy,
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_SECONDARY,
            font=('Segoe UI', 18, 'bold'),
            relief=tk.FLAT,
            bd=0,
            padx=15,
            cursor='hand2',
            activebackground=COLOR_ERROR,
            activeforeground=COLOR_TEXT_PRIMARY
        )
        close_btn.pack(side=tk.RIGHT)
        
        # Content
        content_frame = tk.Frame(container, bg=COLOR_BG_DARK)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        message_label = tk.Label(
            content_frame,
            text=message,
            bg=COLOR_BG_DARK,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 11),
            justify=tk.LEFT,
            wraplength=400
        )
        message_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Buttons
        btn_frame = tk.Frame(content_frame, bg=COLOR_BG_DARK)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        def yes_action():
            self.result = True
            self.dialog.destroy()
        
        def no_action():
            self.result = False
            self.dialog.destroy()
        
        no_btn = tk.Button(
            btn_frame,
            text="No",
            command=no_action,
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            bd=0,
            padx=25,
            pady=10,
            cursor='hand2',
            activebackground=COLOR_BG_HOVER,
            activeforeground=COLOR_TEXT_PRIMARY
        )
        no_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        yes_btn = tk.Button(
            btn_frame,
            text="Yes",
            command=yes_action,
            bg=COLOR_ACCENT,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            bd=0,
            padx=25,
            pady=10,
            cursor='hand2',
            activebackground=COLOR_ACCENT_HOVER,
            activeforeground=COLOR_TEXT_PRIMARY
        )
        yes_btn.pack(side=tk.RIGHT)
        
        self.dialog.bind('<Escape>', lambda e: no_action())
        self.dialog.focus_set()
        yes_btn.focus_set()
    
    def show(self):
        """Show the dialog and return True if Yes, False if No."""
        self.dialog.wait_window()
        return self.result


class BeatlibraryProvenanceApp:
    """Modern dark-themed desktop interface for Beatlibrary Audio Provenance API."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Beatlibrary - Audio Provenance")  # Title for taskbar
        self.root.geometry("1400x950")
        self.root.minsize(1200, 700)  # Minimum window size
        self.root.configure(bg=COLOR_BG_DARK)
        
        # Set icon from icon.ico file - MUST be set before window is shown
        try:
            import os
            from pathlib import Path
            
            # Get the icon.ico file path (in the same directory as this script)
            script_dir = Path(__file__).parent.absolute()
            icon_path = script_dir / "icon.ico"
            
            # Convert to absolute path string (required for iconbitmap)
            icon_path_str = str(icon_path.absolute())
            
            # Check if icon.ico exists
            if icon_path.exists():
                # Store icon path as absolute path
                self.icon_path = icon_path_str
                
                # Set icon using iconbitmap IMMEDIATELY (before window is shown)
                # This is critical for Windows taskbar
                try:
                    self.root.iconbitmap(icon_path_str)
                except Exception as e:
                    print(f"Could not set icon using iconbitmap: {e}")
                
                # Also prepare iconphoto as backup (load images now)
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(icon_path_str)
                    
                    # Create PhotoImage versions in multiple sizes
                    icon_256 = img.resize((256, 256), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
                    icon_128 = img.resize((128, 128), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
                    icon_64 = img.resize((64, 64), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
                    icon_48 = img.resize((48, 48), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
                    icon_32 = img.resize((32, 32), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
                    icon_16 = img.resize((16, 16), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
                    
                    photo_256 = ImageTk.PhotoImage(icon_256)
                    photo_128 = ImageTk.PhotoImage(icon_128)
                    photo_64 = ImageTk.PhotoImage(icon_64)
                    photo_48 = ImageTk.PhotoImage(icon_48)
                    photo_32 = ImageTk.PhotoImage(icon_32)
                    photo_16 = ImageTk.PhotoImage(icon_16)
                    
                    # Keep references to prevent garbage collection
                    self.root.icon_images = (photo_256, photo_128, photo_64, photo_48, photo_32, photo_16)
                    
                    # Also set iconphoto (works together with iconbitmap)
                    self.root.iconphoto(True, photo_256, photo_128, photo_64, photo_48, photo_32, photo_16)
                except Exception as e2:
                    print(f"Could not set icon using iconphoto: {e2}")
            else:
                print(f"Icon file not found: {icon_path}")
                self.icon_path = None
                
        except Exception as e:
            # Icon setting failed, use default
            print(f"Could not set icon: {e}")
            self.icon_path = None
        
        # Title bar will be set to dark/black after window is shown
        
        # Keep window in taskbar (don't use overrideredirect)
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Configure root grid weights for proper layout
        self.root.grid_rowconfigure(0, weight=1)  # Main content row
        self.root.grid_columnconfigure(0, weight=1)
        
        # Configure dark theme
        self.setup_dark_theme()
        
        self.job_id: Optional[str] = None
        self.report: Optional[Dict] = None
        self.viz_generated = False  # Track if visualizations have been generated
        self.pending_updates = []  # Queue for thread-safe UI updates
        self._tags_configured = set()  # Track configured text tags
        self.current_step = 1  # Track current wizard step (1-3)
        self.step_frames = {}  # Store step frame references
        self.update_queue_id = None  # Track the update queue callback ID
        
        self.setup_ui()
        
        # Apply dark title bar after window is shown
        self.root.after(100, self.apply_dark_title_bar)
        
        # Re-apply icon after window is shown (ensures it shows in taskbar)
        self.root.after(300, self._reapply_icon)
        
        # Start update queue processor
        self.update_queue_id = self.root.after(50, self.process_update_queue)
    
    def apply_dark_title_bar(self):
        """Apply dark/black title bar and rounded corners (Windows-specific)."""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Get window handle (need to get it after window is shown)
            try:
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                if hwnd == 0:
                    hwnd = self.root.winfo_id()
            except:
                hwnd = self.root.winfo_id()
            
            # Windows 10/11: Use DWM to enable dark mode title bar (black) and rounded corners
            try:
                dwmapi = ctypes.windll.dwmapi
                
                # Enable dark mode title bar (black)
                DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                value = ctypes.c_int(1)  # Enable dark mode (black title bar)
                
                dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    DWMWA_USE_IMMERSIVE_DARK_MODE,
                    ctypes.byref(value),
                    ctypes.sizeof(value)
                )
                
                # Set rounded corners (Windows 11+)
                # DWMWA_WINDOW_CORNER_PREFERENCE = 33
                # 2 = DWMWCP_ROUND (rounded corners)
                # 1 = DWMWCP_ROUNDSMALL (small rounded corners)
                # 0 = DWMWCP_DEFAULT (system default)
                try:
                    DWMWA_WINDOW_CORNER_PREFERENCE = 33
                    corner_preference = ctypes.c_int(2)  # DWMWCP_ROUND - rounded corners
                    
                    dwmapi.DwmSetWindowAttribute(
                        hwnd,
                        DWMWA_WINDOW_CORNER_PREFERENCE,
                        ctypes.byref(corner_preference),
                        ctypes.sizeof(corner_preference)
                    )
                except Exception:
                    # Rounded corners not supported (Windows 10 or older)
                    pass
                
            except Exception:
                pass
        except Exception:
            pass
    
    def _set_iconbitmap(self, ico_path):
        """Set icon using iconbitmap and Windows API (called after window is shown for better Windows taskbar support)."""
        try:
            import os
            if os.path.exists(ico_path):
                # Use absolute path
                abs_path = os.path.abspath(ico_path)
                self.root.iconbitmap(abs_path)
                
                # Also use Windows API directly to force taskbar icon update
                try:
                    import ctypes
                    from ctypes import wintypes
                    
                    # Get window handle
                    try:
                        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                        if hwnd == 0:
                            hwnd = self.root.winfo_id()
                    except:
                        hwnd = self.root.winfo_id()
                    
                    # Load icon using Windows API
                    IMAGE_ICON = 1
                    LR_LOADFROMFILE = 0x0010
                    
                    # Convert to wide string (Unicode)
                    abs_path_wide = ctypes.create_unicode_buffer(abs_path)
                    
                    # Load small icon (16x16) for taskbar
                    hicon_small = ctypes.windll.user32.LoadImageW(
                        0,
                        abs_path_wide,
                        IMAGE_ICON,
                        16, 16,
                        LR_LOADFROMFILE
                    )
                    
                    # Load large icon (32x32) for window
                    hicon_large = ctypes.windll.user32.LoadImageW(
                        0,
                        abs_path_wide,
                        IMAGE_ICON,
                        32, 32,
                        LR_LOADFROMFILE
                    )
                    
                    # Set icons using Windows messages
                    if hicon_small or hicon_large:
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1
                        
                        if hicon_small:
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
                        if hicon_large:
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_large)
                except Exception as api_error:
                    # Windows API failed, that's okay - iconbitmap should still work
                    pass
        except Exception as e:
            # iconbitmap failed, iconphoto should still work
            pass
    
    def _reapply_icon(self):
        """Re-apply icon after window is fully shown (helps with Windows taskbar)."""
        try:
            # Re-apply iconbitmap with Windows API
            if hasattr(self, 'icon_path') and self.icon_path:
                self._set_iconbitmap(self.icon_path)
            
            # Also re-apply iconphoto as backup
            if hasattr(self, 'root') and hasattr(self.root, 'icon_images'):
                try:
                    self.root.iconphoto(True, *self.root.icon_images)
                except:
                    pass
        except Exception:
            pass
    
    def show_alert(self, title, message, alert_type='info'):
        """Show custom dark-themed alert dialog."""
        alert = CustomAlert(self.root, title, message, alert_type)
        alert.show()
    
    def show_confirm(self, title, message):
        """Show custom dark-themed confirmation dialog. Returns True if Yes, False if No."""
        confirm = CustomConfirm(self.root, title, message)
        return confirm.show()
    
    def setup_dark_theme(self):
        """Configure dark theme for ttk widgets."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure dark theme colors
        style.configure('TFrame', background=COLOR_BG_DARK)
        style.configure('TLabel', background=COLOR_BG_DARK, foreground=COLOR_TEXT_PRIMARY)
        style.configure('TButton', 
                       background=COLOR_ACCENT,
                       foreground=COLOR_TEXT_PRIMARY,
                       borderwidth=0,
                       focuscolor='none',
                       padding=12)
        style.map('TButton',
                 background=[('active', COLOR_ACCENT_HOVER), ('pressed', '#4F46E5')])
        
        style.configure('TEntry',
                       fieldbackground=COLOR_INPUT_BG,
                       foreground=COLOR_TEXT_PRIMARY,
                       borderwidth=1,
                       relief='solid',
                       bordercolor=COLOR_BORDER,
                       padding=8)
        
        style.configure('TNotebook',
                       background=COLOR_BG_DARK,
                       borderwidth=0)
        # Configure tabs with fixed padding and font to prevent size changes
        style.configure('TNotebook.Tab',
                       background=COLOR_BG_CARD,
                       foreground=COLOR_TEXT_SECONDARY,
                       padding=[20, 10],  # [left/right, top/bottom]
                       borderwidth=0,
                       focuscolor='none',  # Remove focus border that might affect size
                       font=('Segoe UI', 10))  # Fixed font to prevent size changes
        # Map selected state - keep same padding and font to prevent size change
        style.map('TNotebook.Tab',
                 background=[('selected', COLOR_ACCENT)],
                 foreground=[('selected', COLOR_TEXT_PRIMARY)],
                 padding=[('selected', [20, 10]), ('!selected', [20, 10])],  # Same padding for both states
                 font=[('selected', ('Segoe UI', 10)), ('!selected', ('Segoe UI', 10))])  # Same font for both states
        
        style.configure('TProgressbar',
                       background=COLOR_ACCENT,
                       troughcolor=COLOR_BG_CARD,
                       borderwidth=0,
                       lightcolor=COLOR_ACCENT,
                       darkcolor=COLOR_ACCENT)
    
    def create_card(self, parent, padx=0, pady=0):
        """Create a dark-themed card frame."""
        card = tk.Frame(
            parent,
            bg=COLOR_BG_CARD,
            relief=tk.FLAT,
            bd=0,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1
        )
        return card
    
    def create_button(self, parent, text, command, style='primary', width=None):
        """Create a styled button."""
        bg_color = COLOR_ACCENT if style == 'primary' else COLOR_BG_CARD
        hover_color = COLOR_ACCENT_HOVER if style == 'primary' else COLOR_BG_HOVER
        fg_color = COLOR_TEXT_PRIMARY
        
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg=fg_color,
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=25,
            pady=12,
            cursor='hand2',
            activebackground=hover_color,
            activeforeground=COLOR_TEXT_PRIMARY,
            width=width
        )
        return btn
    
    def setup_ui(self):
        """Setup wizard-style step-by-step interface."""
        # Main container using grid for better control
        main_container = tk.Frame(self.root, bg=COLOR_BG_DARK)
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=40, pady=30)
        
        # Configure grid weights - step container gets most space, nav frame stays at bottom
        main_container.grid_rowconfigure(2, weight=1)  # Step container row
        main_container.grid_rowconfigure(3, weight=0)  # Nav frame row (fixed)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Header Section (matching first image: title left, progress right)
        header_frame = tk.Frame(main_container, bg=COLOR_BG_DARK)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 30))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)
        
        # Make header draggable for window movement
        def start_drag(event):
            self.drag_start_x = event.x_root - self.root.winfo_x()
            self.drag_start_y = event.y_root - self.root.winfo_y()
        
        def on_drag(event):
            x = event.x_root - self.drag_start_x
            y = event.y_root - self.drag_start_y
            self.root.geometry(f"+{x}+{y}")
        
        header_frame.bind("<Button-1>", start_drag)
        header_frame.bind("<B1-Motion>", on_drag)
        
        # Left side: "Provenance Report" title
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
        
        # Right side: Step Progress Indicator (matching first image design)
        progress_frame = tk.Frame(header_frame, bg=COLOR_BG_DARK)
        progress_frame.grid(row=0, column=1, sticky=tk.E)
        
        self.progress_circles = []  # Store circle canvases
        self.progress_texts = []    # Store text labels
        step_names = ["Connection & Upload", "Processing", "Report"]
        
        for i in range(1, 4):
            # Step container (circle + text)
            step_container = tk.Frame(progress_frame, bg=COLOR_BG_DARK)
            step_container.pack(side=tk.LEFT)
            
            # Step circle (circular design using Canvas)
            circle_canvas = tk.Canvas(
                step_container,
                width=24,
                height=24,
                bg=COLOR_BG_DARK,
                highlightthickness=0
            )
            circle_canvas.pack(side=tk.LEFT, padx=(0, 8))
            
            # Draw circle (dark gray for inactive, purple for active)
            circle_id = circle_canvas.create_oval(
                2, 2, 22, 22,
                fill=COLOR_BG_CARD,  # Dark gray for inactive
                outline="",
                width=0
            )
            
            # Draw number text in center
            text_id = circle_canvas.create_text(
                12, 12,
                text=str(i),
                fill=COLOR_TEXT_SECONDARY,
                font=('Segoe UI', 11, 'bold')
            )
            
            # Store references
            self.progress_circles.append({
                'canvas': circle_canvas,
                'circle': circle_id,
                'text': text_id
            })
            
            # Step name (to the right of circle)
            step_name_label = tk.Label(
                step_container,
                text=step_names[i-1],
                bg=COLOR_BG_DARK,
                fg=COLOR_TEXT_SECONDARY,  # Light gray for inactive
                font=('Segoe UI', 10)
            )
            step_name_label.pack(side=tk.LEFT)
            self.progress_texts.append(step_name_label)
            
            # Purple separator line (except after last step)
            if i < 3:
                separator = tk.Frame(
                    progress_frame,
                    bg=COLOR_ACCENT,  # Purple separator
                    width=2,
                    height=1
                )
                separator.pack(side=tk.LEFT, padx=15, fill=tk.Y, ipady=2)
        
        # Step Container (shows only current step) - with max height constraint
        self.step_container = tk.Frame(main_container, bg=COLOR_BG_DARK)
        self.step_container.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create all step frames (initially hidden)
        self.create_step1()
        self.create_step2()
        self.create_step3()
        
        # Navigation Buttons - Always visible at bottom (fixed height, no expansion)
        nav_frame = tk.Frame(main_container, bg=COLOR_BG_DARK, height=60)
        nav_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(20, 0))
        nav_frame.grid_propagate(False)  # Prevent frame from shrinking below minimum size
        nav_frame.columnconfigure(0, weight=1)
        nav_frame.columnconfigure(1, weight=0)
        
        # Button container to ensure proper spacing
        btn_container = tk.Frame(nav_frame, bg=COLOR_BG_DARK)
        btn_container.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.prev_btn = self.create_button(btn_container, "← Previous", self.previous_step, 'secondary')
        self.prev_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.next_btn = self.create_button(btn_container, "Next →", self.next_step, 'primary')
        self.next_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Ensure nav frame is always on top (z-order)
        nav_frame.lift()
        
        # Initialize to show step 1
        self.show_step(1)
    
    def create_step1(self):
        """Create Step 1: Connection & File Upload."""
        step1_frame = tk.Frame(self.step_container, bg=COLOR_BG_DARK)
        step1_card = self.create_card(step1_frame)
        step1_card.pack(fill=tk.BOTH, expand=True)
        
        # Use grid layout for better control - no scrolling needed
        step1_inner = tk.Frame(step1_card, bg=COLOR_BG_CARD, padx=40, pady=25)
        step1_inner.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        step1_card.grid_rowconfigure(0, weight=1)
        step1_card.grid_columnconfigure(0, weight=1)
        
        # Configure grid for vertical centering
        step1_inner.grid_rowconfigure(0, weight=1)  # Top spacer
        step1_inner.grid_rowconfigure(1, weight=0)  # API Connection
        step1_inner.grid_rowconfigure(2, weight=0)  # Upload section
        step1_inner.grid_rowconfigure(3, weight=0)  # File info
        step1_inner.grid_rowconfigure(4, weight=0)  # Progress bar
        step1_inner.grid_rowconfigure(5, weight=0)  # Upload button
        step1_inner.grid_rowconfigure(6, weight=1)  # Bottom spacer
        step1_inner.grid_columnconfigure(0, weight=1)
        
        # Row 0: Top spacer (for vertical centering)
        top_spacer = tk.Frame(step1_inner, bg=COLOR_BG_CARD, height=1)
        top_spacer.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Row 1: API Connection Section
        api_section = tk.Frame(step1_inner, bg=COLOR_BG_CARD)
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
        
        self.url_var = tk.StringVar(value=BASE_URL)
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
        
        test_btn = self.create_button(api_section, "Test Connection", self.test_health, 'primary')
        test_btn.grid(row=1, column=2, sticky=tk.W)
        
        # Row 2: Upload Audio File Section
        upload_section = tk.Frame(step1_inner, bg=COLOR_BG_CARD)
        upload_section.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        upload_section.grid_columnconfigure(0, weight=1)
        
        tk.Label(
            upload_section,
            text="Upload Audio File",
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 16, 'bold')
        ).grid(row=0, column=0, sticky=tk.W, pady=(0, 12))
        
        # Drag and Drop Area (clean, always visible design)
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
        
        # Inner container for drop area content
        self.drop_content = tk.Frame(self.drop_frame, bg=COLOR_BG_CARD)
        self.drop_content.pack(expand=True, fill=tk.BOTH)
        
        # Cloud icon
        self.cloud_icon_label = tk.Label(
            self.drop_content,
            text="☁",
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 36)
        )
        self.cloud_icon_label.pack(pady=(12, 8))
        
        # Drag & drop text
        self.drop_text1 = tk.Label(
            self.drop_content,
            text="Drag & drop your audio file here",
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 13, 'bold')
        )
        self.drop_text1.pack(pady=(0, 4))
        
        self.drop_text2 = tk.Label(
            self.drop_content,
            text="or click to browse",
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_SECONDARY,
            font=('Segoe UI', 11)
        )
        self.drop_text2.pack()
        
        # Make drop area clickable
        self.drop_frame.bind("<Button-1>", lambda e: self.browse_file())
        self.drop_frame.bind("<Enter>", lambda e: self.drop_frame.config(highlightbackground=COLOR_ACCENT))
        self.drop_frame.bind("<Leave>", lambda e: self.drop_frame.config(highlightbackground="#666666"))
        self.drop_content.bind("<Button-1>", lambda e: self.browse_file())
        self.cloud_icon_label.bind("<Button-1>", lambda e: self.browse_file())
        self.drop_text1.bind("<Button-1>", lambda e: self.browse_file())
        self.drop_text2.bind("<Button-1>", lambda e: self.browse_file())
        
        # Row 3: Selected File Display (clean, professional design)
        self.file_info_frame = tk.Frame(step1_inner, bg=COLOR_BG_CARD, height=50)
        self.file_info_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        self.file_info_frame.grid_propagate(False)  # Maintain fixed height
        self.file_info_frame.grid_columnconfigure(1, weight=1)
        
        self.file_var = tk.StringVar()
        self.selected_file = None
        self.file_size_mb = 0
        
        # File display container (clean design matching image)
        self.file_display_container = tk.Frame(self.file_info_frame, bg=COLOR_BG_CARD)
        self.file_display_container.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=0, pady=5)
        self.file_display_container.grid_columnconfigure(1, weight=1)
        self.file_display_container.grid_remove()  # Hidden initially
        
        # File name and size display (left side - clean text)
        self.file_name_label = tk.Label(
            self.file_display_container,
            text="",
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 11),
            anchor=tk.W
        )
        self.file_name_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 15))
        
        # File path display (right side - entry field style, readonly)
        self.file_path_entry = tk.Entry(
            self.file_display_container,
            textvariable=self.file_var,
            font=('Segoe UI', 10),
            bg=COLOR_INPUT_BG,  # Dark input background (#0F0F0F)
            fg=COLOR_TEXT_SECONDARY,
            insertbackground=COLOR_TEXT_PRIMARY,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_ACCENT,
            readonlybackground=COLOR_INPUT_BG,  # Dark background for readonly state
            state='readonly',
            width=30
        )
        self.file_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10), ipady=6)
        
        # Remove file button (X) - subtle, clean design
        self.remove_file_btn = tk.Button(
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
        self.remove_file_btn.grid(row=0, column=2, sticky=tk.E)
        
        # Row 4: Upload Progress Bar
        upload_progress_frame = tk.Frame(step1_inner, bg=COLOR_BG_CARD)
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
        
        # Row 5: Upload button (directly below progress bar)
        upload_btn = self.create_button(
            step1_inner,
            "Upload & Process Track",
            self.upload_and_process,
            'primary'
        )
        upload_btn.grid(row=5, column=0, sticky=tk.W, pady=(0, 0))
        
        # Row 6: Bottom spacer (for vertical centering)
        bottom_spacer = tk.Frame(step1_inner, bg=COLOR_BG_CARD, height=1)
        bottom_spacer.grid(row=6, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.step_frames[1] = step1_frame
    
    def create_step2(self):
        """Create Step 2: Processing Status."""
        step2_frame = tk.Frame(self.step_container, bg=COLOR_BG_DARK)
        step2_card = self.create_card(step2_frame)
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
        
        self.status_var = tk.StringVar(value="Ready to process")
        status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 14)
        )
        status_label.pack(anchor=tk.W)
        
        # Progress bar (can be determinate or indeterminate)
        progress_frame = tk.Frame(step2_inner, bg=COLOR_BG_CARD)
        progress_frame.pack(fill=tk.X, pady=(10, 20))
        
        self.progress = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=600,
            maximum=100
        )
        self.progress.pack(fill=tk.X)
        
        # Progress percentage label
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
        
        self.job_id_var = tk.StringVar()
        job_id_label = tk.Label(
            job_frame,
            textvariable=self.job_id_var,
            bg=COLOR_BG_CARD,
            fg=COLOR_ACCENT,
            font=('Consolas', 11)
        )
        job_id_label.pack(side=tk.LEFT)
        
        # Action buttons
        action_frame = tk.Frame(step2_inner, bg=COLOR_BG_CARD)
        action_frame.pack(fill=tk.X)
        
        check_btn = self.create_button(action_frame, "Check Status", self.check_status, 'secondary')
        check_btn.pack(side=tk.LEFT, padx=(0, 12))
        
        download_btn = self.create_button(action_frame, "Download Report", self.download_report, 'primary')
        download_btn.pack(side=tk.LEFT)
        
        self.step_frames[2] = step2_frame
    
    def create_step3(self):
        """Create Step 3: Report Display."""
        step3_frame = tk.Frame(self.step_container, bg=COLOR_BG_DARK)
        step3_card = self.create_card(step3_frame)
        step3_card.pack(fill=tk.BOTH, expand=True)
        
        step3_inner = tk.Frame(step3_card, bg=COLOR_BG_CARD, padx=40, pady=40)
        step3_inner.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            step3_inner,
            text="Provenance Report",
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 16, 'bold')
        ).pack(anchor=tk.W, pady=(0, 20))
        
        # Report display with tabs
        notebook = ttk.Notebook(step3_inner)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Summary tab - 2-column layout (no scrolling needed)
        summary_frame = tk.Frame(notebook, bg=COLOR_BG_CARD)
        notebook.add(summary_frame, text="  Summary  ")
        
        # Create 2-column layout
        summary_frame.grid_columnconfigure(0, weight=1)
        summary_frame.grid_columnconfigure(1, weight=1)
        summary_frame.grid_rowconfigure(0, weight=1)
        
        # Left column
        left_column = tk.Frame(summary_frame, bg=COLOR_BG_DARK)
        left_column.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(25, 12), pady=25)
        
        left_text = tk.Text(
            left_column,
            wrap=tk.WORD,
            font=('Segoe UI', 11),
            bg=COLOR_BG_DARK,
            fg=COLOR_TEXT_SECONDARY,
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=15,
            insertbackground=COLOR_TEXT_PRIMARY,
            selectbackground=COLOR_ACCENT,
            selectforeground=COLOR_TEXT_PRIMARY,
            state='disabled'  # Make read-only
        )
        left_text.pack(fill=tk.BOTH, expand=True)
        self.summary_text_left = left_text
        
        # Right column
        right_column = tk.Frame(summary_frame, bg=COLOR_BG_DARK)
        right_column.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(12, 25), pady=25)
        
        right_text = tk.Text(
            right_column,
            wrap=tk.WORD,
            font=('Segoe UI', 11),
            bg=COLOR_BG_DARK,
            fg=COLOR_TEXT_SECONDARY,
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=15,
            insertbackground=COLOR_TEXT_PRIMARY,
            selectbackground=COLOR_ACCENT,
            selectforeground=COLOR_TEXT_PRIMARY,
            state='disabled'  # Make read-only
        )
        right_text.pack(fill=tk.BOTH, expand=True)
        self.summary_text_right = right_text
        
        # Keep reference to left for backward compatibility
        self.summary_text = left_text
        
        # Details tab
        details_frame = tk.Frame(notebook, bg=COLOR_BG_CARD)
        notebook.add(details_frame, text="  Full Report  ")
        
        details_scroll = scrolledtext.ScrolledText(
            details_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg=COLOR_BG_DARK,
            fg=COLOR_TEXT_SECONDARY,
            relief=tk.FLAT,
            bd=0,
            padx=25,
            pady=25,
            insertbackground=COLOR_TEXT_PRIMARY,
            selectbackground=COLOR_ACCENT,
            selectforeground=COLOR_TEXT_PRIMARY
        )
        details_scroll.pack(fill=tk.BOTH, expand=True)
        self.details_text = details_scroll
        
        # Visualizations tab
        viz_frame = tk.Frame(notebook, bg=COLOR_BG_CARD)
        notebook.add(viz_frame, text="  📊 Visualizations  ")
        
        # Scrollable canvas for visualizations
        viz_canvas = tk.Canvas(viz_frame, bg=COLOR_BG_DARK, highlightthickness=0)
        viz_scrollbar = ttk.Scrollbar(viz_frame, orient="vertical", command=viz_canvas.yview)
        viz_scrollable = tk.Frame(viz_canvas, bg=COLOR_BG_DARK)
        
        def update_scroll_region(event):
            """Update scroll region when content changes."""
            viz_canvas.configure(scrollregion=viz_canvas.bbox("all"))
        
        viz_scrollable.bind("<Configure>", update_scroll_region)
        
        # Create canvas window - make it expand with content
        canvas_window_id = viz_canvas.create_window((0, 0), window=viz_scrollable, anchor="nw")
        viz_canvas.configure(yscrollcommand=viz_scrollbar.set)
        
        # Make canvas window expand to fill canvas width
        # Height will be set by grid layout after charts are created
        def on_canvas_configure(event):
            """Update canvas window width when canvas is resized."""
            canvas_width = event.width
            # Use full canvas width to fill the interface
            try:
                current_height = viz_canvas.itemcget(canvas_window_id, 'height')
                if current_height and current_height != '':
                    # Preserve height set by grid, use full canvas width
                    viz_canvas.itemconfig(canvas_window_id, width=canvas_width, height=current_height)
                else:
                    # Let content determine height initially, use full canvas width
                    viz_canvas.itemconfig(canvas_window_id, width=canvas_width)
            except:
                # Fallback: just set width to canvas width
                viz_canvas.itemconfig(canvas_window_id, width=canvas_width)
        
        viz_canvas.bind('<Configure>', on_canvas_configure)
        
        # Store canvas window ID for later updates
        self.viz_canvas_window_id = canvas_window_id
        
        viz_canvas.pack(side="left", fill="both", expand=True)
        viz_scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel for viz canvas
        def on_viz_mousewheel(event):
            viz_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        viz_canvas.bind_all("<MouseWheel>", on_viz_mousewheel)
        
        self.viz_container = viz_scrollable
        self.viz_canvas = viz_canvas
        
        # Bind tab change event for lazy loading
        def on_tab_changed(event):
            selected = event.widget.tab('current')['text'].strip()
            if 'Visualizations' in selected and self.report and not self.viz_generated:
                self.schedule_viz_generation()
        
        notebook.bind('<<NotebookTabChanged>>', on_tab_changed)
        
        # Logs tab
        logs_frame = tk.Frame(notebook, bg=COLOR_BG_CARD)
        notebook.add(logs_frame, text="  Processing Logs  ")
        
        logs_scroll = scrolledtext.ScrolledText(
            logs_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg=COLOR_BG_DARK,
            fg=COLOR_TEXT_SECONDARY,
            relief=tk.FLAT,
            bd=0,
            padx=25,
            pady=25,
            insertbackground=COLOR_TEXT_PRIMARY,
            selectbackground=COLOR_ACCENT,
            selectforeground=COLOR_TEXT_PRIMARY
        )
        logs_scroll.pack(fill=tk.BOTH, expand=True)
        self.log_text = logs_scroll
        
        self.step_frames[3] = step3_frame
    
    def show_step(self, step_num):
        """Show the specified step and hide others."""
        self.current_step = step_num
        
        # Hide all steps
        for step_frame in self.step_frames.values():
            step_frame.pack_forget()
        
        # Show current step
        if step_num in self.step_frames:
            self.step_frames[step_num].pack(fill=tk.BOTH, expand=True)
        
        # Force layout update and ensure buttons are visible
        self.root.update_idletasks()
        
        # Scroll to show navigation buttons if they're out of view
        # This ensures buttons are always accessible
        try:
            # Get the navigation frame and ensure it's visible
            nav_frame = self.prev_btn.master
            nav_frame.update_idletasks()
            # Force the window to show the navigation area
            self.root.see(nav_frame) if hasattr(self.root, 'see') else None
        except:
            pass
        
        # Update progress indicators (matching first image design)
        for i in range(1, 4):
            circle_idx = i - 1
            if circle_idx < len(self.progress_circles) and circle_idx < len(self.progress_texts):
                circle_data = self.progress_circles[circle_idx]
                text_label = self.progress_texts[circle_idx]
                
                if i < step_num:
                    # Completed step - dark gray circle, light gray text
                    circle_data['canvas'].itemconfig(circle_data['circle'], fill=COLOR_BG_CARD)
                    circle_data['canvas'].itemconfig(circle_data['text'], fill=COLOR_TEXT_SECONDARY)
                    text_label.config(fg=COLOR_TEXT_SECONDARY)
                elif i == step_num:
                    # Current step - purple circle, white text in circle, lighter purple text label
                    circle_data['canvas'].itemconfig(circle_data['circle'], fill=COLOR_ACCENT)
                    circle_data['canvas'].itemconfig(circle_data['text'], fill=COLOR_TEXT_PRIMARY)
                    text_label.config(fg=COLOR_ACCENT_HOVER)  # Lighter purple for active text
                else:
                    # Future step - dark gray circle, light gray text
                    circle_data['canvas'].itemconfig(circle_data['circle'], fill=COLOR_BG_CARD)
                    circle_data['canvas'].itemconfig(circle_data['text'], fill=COLOR_TEXT_SECONDARY)
                    text_label.config(fg=COLOR_TEXT_SECONDARY)
        
        # Update navigation buttons based on step completion
        # Previous button: enabled on steps 2-3, disabled on step 1
        if step_num > 1:
            self.prev_btn.config(
                state=tk.NORMAL, 
                cursor='hand2',
                bg=COLOR_BG_CARD,
                fg=COLOR_TEXT_PRIMARY,
                activebackground=COLOR_BG_HOVER,
                activeforeground=COLOR_TEXT_PRIMARY
            )
        else:
            self.prev_btn.config(
                state=tk.DISABLED, 
                cursor='arrow',
                bg=COLOR_BG_CARD, 
                fg=COLOR_TEXT_SECONDARY,
                disabledforeground=COLOR_TEXT_SECONDARY
            )
        
        # Next button logic - only enabled if current step is completed
        if step_num == 1:
            # Step 1 complete when file is uploaded (job_id exists)
            step1_complete = self.job_id is not None
            if step1_complete:
                self.next_btn.config(
                    state=tk.NORMAL, 
                    text="Next →", 
                    cursor='hand2',
                    bg=COLOR_ACCENT, 
                    fg=COLOR_TEXT_PRIMARY,
                    activebackground=COLOR_ACCENT_HOVER,
                    activeforeground=COLOR_TEXT_PRIMARY
                )
            else:
                self.next_btn.config(
                    state=tk.DISABLED, 
                    text="Next → (Upload file first)", 
                    cursor='arrow',
                    bg=COLOR_BG_CARD, 
                    fg=COLOR_TEXT_SECONDARY,
                    disabledforeground=COLOR_TEXT_SECONDARY
                )
        elif step_num == 2:
            # Step 2 complete when report is downloaded (report exists)
            step2_complete = self.report is not None
            if step2_complete:
                self.next_btn.config(
                    state=tk.NORMAL, 
                    text="Next →", 
                    cursor='hand2',
                    bg=COLOR_ACCENT, 
                    fg=COLOR_TEXT_PRIMARY,
                    activebackground=COLOR_ACCENT_HOVER,
                    activeforeground=COLOR_TEXT_PRIMARY
                )
            else:
                self.next_btn.config(
                    state=tk.DISABLED, 
                    text="Next → (Download report first)", 
                    cursor='arrow',
                    bg=COLOR_BG_CARD, 
                    fg=COLOR_TEXT_SECONDARY,
                    disabledforeground=COLOR_TEXT_SECONDARY
                )
        else:
            # Last step - show as complete
            self.next_btn.config(
                state=tk.DISABLED, 
                text="Complete", 
                cursor='arrow',
                bg=COLOR_BG_CARD, 
                fg=COLOR_TEXT_SECONDARY,
                disabledforeground=COLOR_TEXT_SECONDARY
            )
    
    def next_step(self):
        """Navigate to next step only if current step is completed."""
        # Check if current step is completed
        if self.current_step == 1:
            # Step 1: Must have uploaded file (job_id exists)
            if not self.job_id:
                self.show_alert(
                    "Step Not Complete",
                    "Please upload an audio file first before proceeding to the next step.",
                    'warning'
                )
                return
        elif self.current_step == 2:
            # Step 2: Must have downloaded report (report exists)
            if not self.report:
                self.show_alert(
                    "Step Not Complete",
                    "Please download the report first before proceeding to the next step.",
                    'warning'
                )
                return
        
        # Proceed to next step if current step is completed
        if self.current_step < 3:
            self.show_step(self.current_step + 1)
    
    def previous_step(self):
        """Navigate to previous step."""
        if self.current_step > 1:
            self.show_step(self.current_step - 1)
    
    def process_update_queue(self):
        """Process pending UI updates from background threads."""
        if not hasattr(self, 'root') or not self.root.winfo_exists():
            return  # Window destroyed, stop processing
        
        while self.pending_updates:
            func, args, kwargs = self.pending_updates.pop(0)
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"Error in UI update: {e}")
        
        # Schedule next check only if window still exists
        if hasattr(self, 'root') and self.root.winfo_exists():
            self.update_queue_id = self.root.after(50, self.process_update_queue)
    
    def safe_update(self, func, *args, **kwargs):
        """Queue a UI update to be executed in the main thread."""
        self.pending_updates.append((func, args, kwargs))
    
    def log(self, message: str, level: str = "INFO"):
        """Add color-coded message to log (thread-safe)."""
        timestamp = time.strftime("%H:%M:%S")
        color_map = {
            "INFO": "#60A5FA",
            "SUCCESS": COLOR_SUCCESS,
            "WARNING": COLOR_WARNING,
            "ERROR": COLOR_ERROR
        }
        color = color_map.get(level, COLOR_TEXT_SECONDARY)
        
        # Batch text insertion for better performance
        full_message = f"[{timestamp}] [{level}] {message}\n"
        
        def update_log():
            self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
            self.log_text.insert(tk.END, f"[{level}] ", level.lower())
            self.log_text.insert(tk.END, f"{message}\n")
            
            # Configure tags (only once per level)
            if "timestamp" not in self._tags_configured:
                self.log_text.tag_config("timestamp", foreground="#666666")
                self._tags_configured.add("timestamp")
            
            if level.lower() not in self._tags_configured:
                self.log_text.tag_config(level.lower(), foreground=color, font=('Consolas', 10, 'bold'))
                self._tags_configured.add(level.lower())
            
            # Only scroll if near the end (reduces redraws)
            if self.log_text.index(tk.END).split('.')[0] == self.log_text.index('end-1c').split('.')[0]:
                self.log_text.see(tk.END)
        
        # Use after() for thread-safe updates
        self.root.after(0, update_log)
    
    def test_health(self):
        """Test health endpoint."""
        def run_test():
            self.root.after(0, lambda: self.progress.config(mode='indeterminate'))
            self.root.after(0, lambda: self.progress.start())
            self.root.after(0, lambda: self.progress_label.config(text="Testing connection..."))
            self.root.after(0, lambda: self.status_var.set("Testing connection..."))
            self.log("Testing API health endpoint...", "INFO")
            
            try:
                url = self.url_var.get()
                response = requests.get(f"{url}/health", timeout=CONNECT_TIMEOUT)
                
                if response.status_code == 200:
                    data = response.json()
                    self.log(f"✅ Connection successful: {data}", "SUCCESS")
                    self.status_var.set("✅ Connected")
                    self.show_alert("Success", f"Connection successful!\n\n{json.dumps(data, indent=2)}", 'success')
                else:
                    self.log(f"❌ Connection failed: {response.status_code}", "ERROR")
                    self.status_var.set("❌ Connection failed")
                    self.show_alert("Error", f"Connection failed: {response.status_code}", 'error')
            except requests.exceptions.Timeout:
                self.log("❌ Connection timeout", "ERROR")
                self.status_var.set("❌ Timeout")
                self.show_alert("Timeout", "Connection timeout!\n\nCheck if API server is running.", 'error')
            except requests.exceptions.ConnectionError as e:
                self.log(f"❌ Connection error: {e}", "ERROR")
                self.status_var.set("❌ Connection Error")
                self.show_alert("Connection Error", f"Cannot connect to API!\n\n{e}", 'error')
            except Exception as e:
                self.log(f"❌ Error: {e}", "ERROR")
                self.root.after(0, lambda: self.status_var.set("❌ Error"))
                self.show_alert("Error", f"Error: {e}", 'error')
            finally:
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.progress_label.config(text=""))
        
        threading.Thread(target=run_test, daemon=True).start()
    
    def browse_file(self):
        """Browse for audio file."""
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
            self.selected_file = filename
            self.file_var.set(filename)
            self.file_size_mb = Path(filename).stat().st_size / (1024 * 1024)
            
            # Keep drop area visible but show file info below
            # Update file display
            file_name = Path(filename).name
            file_ext = Path(filename).suffix.lower().replace('.', '')
            display_name = f"{file_name} ({self.file_size_mb:.1f} MB)"
            
            self.file_name_label.config(text=display_name)
            self.file_display_container.grid()  # Show file display
            
            self.log(f"Selected file: {file_name} ({self.file_size_mb:.2f} MB)", "INFO")
    
    def remove_file(self):
        """Remove selected file and reset drop area."""
        self.selected_file = None
        self.file_var.set("")
        self.file_size_mb = 0
        
        # Hide file display (but keep frame visible to maintain height)
        self.file_display_container.grid_remove()
        
        # Drop area is always visible, no need to re-show elements
        
        # Reset progress
        self.upload_progress.config(value=0)
        self.upload_progress_label.config(text="")
        
        self.log("File selection removed", "INFO")
    
    def upload_and_process(self):
        """Upload file and start processing."""
        filename = self.selected_file or self.file_var.get()
        if not filename or not Path(filename).exists():
            self.show_alert("Error", "Please select a valid audio file", 'error')
            return
        
        # Calculate dynamic timeout
        file_path = Path(filename)
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        dynamic_timeout = min(
            BASE_UPLOAD_TIMEOUT + (file_size_mb * UPLOAD_TIMEOUT_PER_MB),
            MAX_UPLOAD_TIMEOUT
        )
        
        # Warn for large files
        if file_size_mb > 50:
            proceed = self.show_confirm(
                "Large File Warning",
                f"File size: {file_size_mb:.1f} MB\n"
                f"Estimated processing time: {dynamic_timeout // 60} minutes\n\n"
                f"Large files may take longer to process.\nContinue?"
            )
            if not proceed:
                return
        
        def run_upload():
            # Switch to determinate mode and reset (for both Step 1 and Step 2 progress bars)
            self.root.after(0, lambda: self.upload_progress.config(mode='determinate', maximum=100, value=0))
            self.root.after(0, lambda: self.upload_progress_label.config(text="0% - Starting upload..."))
            self.root.after(0, lambda: self.progress.config(mode='determinate', maximum=100, value=0))
            self.root.after(0, lambda: self.progress_label.config(text="0%"))
            self.root.after(0, lambda: self.status_var.set("Uploading track..."))
            self.log(f"Uploading: {Path(filename).name}", "INFO")
            self.log(f"File size: {file_size_mb:.2f} MB", "INFO")
            
            try:
                url = self.url_var.get()
                file_size = file_path.stat().st_size
                
                # Progress tracking variables
                uploaded_bytes = [0]  # Use list to allow modification in nested function
                last_update_time = [time.time()]
                update_interval = 0.05  # Update UI every 50ms for smooth progress
                
                def update_progress(uploaded, total):
                    """Update progress bars in main thread (both Step 1 and Step 2)."""
                    if total > 0:
                        percent = min(int((uploaded / total) * 100), 100)  # Cap at 100%
                        # Update Step 1 progress bar
                        self.root.after(0, lambda p=percent: self.upload_progress.config(value=p))
                        self.root.after(0, lambda p=percent, u=uploaded, t=total: 
                            self.upload_progress_label.config(
                                text=f"{p}% ({u / (1024*1024):.2f} MB / {t / (1024*1024):.2f} MB)"
                            ))
                        # Update Step 2 progress bar (if visible)
                        self.root.after(0, lambda p=percent: self.progress.config(value=p))
                        self.root.after(0, lambda p=percent, u=uploaded, t=total: 
                            self.progress_label.config(
                                text=f"{p}% ({u / (1024*1024):.2f} MB / {t / (1024*1024):.2f} MB)"
                            ))
                
                # Use requests-toolbelt for proper streaming upload with progress
                # If not available, fall back to manual multipart encoding
                try:
                    from requests_toolbelt.multipart.encoder import MultipartEncoder
                    from requests_toolbelt import MultipartEncoderMonitor
                    
                    # Create a callback for progress monitoring
                    def progress_callback(monitor):
                        uploaded_bytes[0] = monitor.bytes_read
                        current_time = time.time()
                        if current_time - last_update_time[0] >= update_interval or uploaded_bytes[0] >= file_size:
                            update_progress(uploaded_bytes[0], file_size)
                            last_update_time[0] = current_time
                    
                    # Create multipart encoder with file
                    with open(filename, 'rb') as f:
                        encoder = MultipartEncoder(
                            fields={'file': (Path(filename).name, f, 'audio/wav')}
                        )
                        
                        # Create monitor with callback
                        monitor = MultipartEncoderMonitor(encoder, progress_callback)
                        
                        # Send request
                        headers = {'Content-Type': monitor.content_type}
                        response = requests.post(
                            f"{url}/api/v1/provenance-check",
                            data=monitor,
                            headers=headers,
                            timeout=dynamic_timeout
                        )
                    
                    # Final progress update
                    update_progress(file_size, file_size)
                    
                except ImportError:
                    # Fallback: Manual multipart encoding with chunked reading
                    import io
                    
                    boundary = '----WebKitFormBoundary' + ''.join([str(i) for i in range(15)])
                    CRLF = b'\r\n'
                    
                    def encode_multipart_with_progress():
                        """Encode multipart form data with progress tracking."""
                        body_parts = []
                        
                        # Add file field header
                        body_parts.append(f'--{boundary}'.encode())
                        body_parts.append(CRLF)
                        body_parts.append(f'Content-Disposition: form-data; name="file"; filename="{Path(filename).name}"'.encode())
                        body_parts.append(CRLF)
                        body_parts.append(b'Content-Type: audio/wav')
                        body_parts.append(CRLF)
                        body_parts.append(CRLF)
                        
                        # Read and add file data in chunks
                        chunk_size = 64 * 1024  # 64KB chunks
                        with open(filename, 'rb') as f:
                            while True:
                                chunk = f.read(chunk_size)
                                if not chunk:
                                    break
                                body_parts.append(chunk)
                                uploaded_bytes[0] += len(chunk)
                                
                                # Update progress
                                current_time = time.time()
                                if current_time - last_update_time[0] >= update_interval or uploaded_bytes[0] >= file_size:
                                    update_progress(uploaded_bytes[0], file_size)
                                    last_update_time[0] = current_time
                        
                        body_parts.append(CRLF)
                        body_parts.append(f'--{boundary}--'.encode())
                        body_parts.append(CRLF)
                        
                        return b''.join(body_parts), f'multipart/form-data; boundary={boundary}'
                    
                    # Encode and send
                    data, content_type = encode_multipart_with_progress()
                    headers = {'Content-Type': content_type}
                    response = requests.post(
                        f"{url}/api/v1/provenance-check",
                        data=data,
                        headers=headers,
                        timeout=dynamic_timeout
                    )
                    
                    # Final progress update
                    update_progress(file_size, file_size)
                
                if response.status_code == 200:
                    # Complete progress bars (both Step 1 and Step 2)
                    self.root.after(0, lambda: self.upload_progress.config(value=100))
                    self.root.after(0, lambda: self.upload_progress_label.config(text="100% - Upload Complete!"))
                    self.root.after(0, lambda: self.progress.config(value=100))
                    self.root.after(0, lambda: self.progress_label.config(text="100% - Upload Complete!"))
                    
                    data = response.json()
                    self.job_id = data.get('job_id')
                    self.job_id_var.set(self.job_id)
                    self.log(f"✅ Upload successful", "SUCCESS")
                    self.log(f"Job ID: {self.job_id}", "INFO")
                    self.root.after(0, lambda: self.status_var.set("✅ Uploaded - Processing..."))
                    self.show_alert(
                        "Success",
                        f"Track uploaded successfully!\n\n"
                        f"Job ID: {self.job_id}\n\n"
                        f"Processing has started. Click 'Next' to monitor progress.",
                        'success'
                    )
                    # Update navigation to reflect step 1 completion and auto-advance to step 2
                    self.root.after(0, lambda: self.show_step(2))
                    self.root.after(0, lambda: self.auto_check_status())
                else:
                    self.log(f"❌ Upload failed: {response.status_code}", "ERROR")
                    self.root.after(0, lambda: self.status_var.set("❌ Upload failed"))
                    self.root.after(0, lambda: self.upload_progress_label.config(text="Upload Failed"))
                    self.root.after(0, lambda: self.progress_label.config(text="Upload Failed"))
                    self.show_alert("Error", f"Upload failed: {response.status_code}\n{response.text}", 'error')
            except requests.exceptions.Timeout:
                self.log(f"❌ Upload timeout after {dynamic_timeout // 60} minutes", "ERROR")
                self.root.after(0, lambda: self.status_var.set("❌ Upload Timeout"))
                self.root.after(0, lambda: self.upload_progress_label.config(text="Upload Timeout"))
                self.root.after(0, lambda: self.progress_label.config(text="Upload Timeout"))
                self.show_alert("Timeout", 
                    f"Upload timeout!\n\n"
                    f"File size: {file_size_mb:.2f} MB\n\n"
                    f"Try a smaller file or check your connection.",
                    'error')
            except Exception as e:
                self.log(f"❌ Error: {e}", "ERROR")
                self.root.after(0, lambda: self.status_var.set("❌ Error"))
                self.root.after(0, lambda: self.upload_progress_label.config(text="Upload Error"))
                self.root.after(0, lambda: self.progress_label.config(text="Upload Error"))
                self.show_alert("Error", f"Upload error: {e}", 'error')
            finally:
                # Reset progress labels after a delay
                self.root.after(2000, lambda: self.upload_progress_label.config(text=""))
                self.root.after(2000, lambda: self.progress_label.config(text=""))
        
        threading.Thread(target=run_upload, daemon=True).start()
    
    def auto_check_status(self):
        """Automatically check status until complete."""
        if not self.job_id:
            return
        
        def check_loop():
            self.log("Waiting for processing to complete...", "INFO")
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
                        self.status_var.set(f"Status: {status.title()}")
                        
                        if status == "completed":
                            self.log("✅ Processing completed!", "SUCCESS")
                            elapsed = time.time() - start_time
                            self.log(f"Processing time: {elapsed:.1f} seconds", "INFO")
                            self.root.after(0, lambda: self.status_var.set("✅ Processing Complete"))
                            self.root.after(0, lambda: self.show_alert(
                                "Success",
                                "Processing completed!\n\n"
                                "Click 'Download Report' to view full provenance results.",
                                'success'
                            ))
                            break
                        elif status == "failed":
                            error = data.get('error', 'Unknown error')
                            self.log(f"❌ Processing failed: {error}", "ERROR")
                            self.root.after(0, lambda: self.status_var.set("❌ Processing failed"))
                            self.root.after(0, lambda e=error: self.show_alert("Error", f"Processing failed:\n{e}", 'error'))
                            break
                        else:
                            elapsed = time.time() - start_time
                            # Only log status every 5 seconds to reduce UI updates
                            if int(elapsed) % 5 == 0:
                                self.log(f"Status: {status} (elapsed: {elapsed:.1f}s)", "INFO")
                            self.root.after(0, lambda s=status: self.status_var.set(f"Status: {s.title()}"))
                    
                    # Adaptive polling: faster when processing, slower when waiting
                    sleep_time = 2 if status == "processing" else 5
                    time.sleep(sleep_time)
                    
                    if time.time() - start_time > MAX_WAIT:
                        self.log(f"⏱️ Timeout after {MAX_WAIT}s", "WARNING")
                        self.root.after(0, lambda: self.status_var.set("⏱️ Timeout"))
                        self.root.after(0, lambda: self.show_alert("Timeout", f"Processing timeout after {MAX_WAIT}s", 'warning'))
                        break
                except Exception as e:
                    self.log(f"❌ Status check error: {e}", "ERROR")
                    time.sleep(2)
        
        threading.Thread(target=check_loop, daemon=True).start()
    
    def check_status(self):
        """Check job status manually."""
        if not self.job_id:
            self.show_alert("Warning", "No job ID. Please upload a file first.", 'warning')
            return
        
        def run_check():
            self.root.after(0, lambda: self.progress.config(mode='indeterminate'))
            self.root.after(0, lambda: self.progress.start())
            self.root.after(0, lambda: self.progress_label.config(text="Checking status..."))
            self.root.after(0, lambda: self.status_var.set("Checking status..."))
            self.log(f"Checking status for job: {self.job_id}", "INFO")
            
            try:
                url = self.url_var.get()
                response = requests.get(
                    f"{url}/api/v1/status/{self.job_id}",
                    timeout=CONNECT_TIMEOUT
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    self.log(f"Status: {status}", "INFO")
                    self.status_var.set(f"Status: {status.title()}")
                    
                    if status == "completed":
                        self.log("✅ Processing completed!", "SUCCESS")
                    elif status == "failed":
                        error = data.get('error', 'Unknown error')
                        self.log(f"❌ Processing failed: {error}", "ERROR")
                    else:
                        self.log(f"⏳ Still processing...", "INFO")
                    
                    self.show_alert("Status", json.dumps(data, indent=2), 'info')
                else:
                    self.log(f"❌ Status check failed: {response.status_code}", "ERROR")
                    self.status_var.set("❌ Status check failed")
                    self.show_alert("Error", f"Status check failed: {response.status_code}", 'error')
            except Exception as e:
                self.log(f"❌ Error: {e}", "ERROR")
                self.root.after(0, lambda: self.status_var.set("❌ Error"))
                self.show_alert("Error", f"Status check error: {e}", 'error')
            finally:
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.progress_label.config(text=""))
        
        threading.Thread(target=run_check, daemon=True).start()
    
    def download_report(self):
        """Download and display report."""
        if not self.job_id:
            self.show_alert("Warning", "No job ID. Please upload a file first.", 'warning')
            return
        
        def run_download():
            self.root.after(0, lambda: self.progress.config(mode='indeterminate'))
            self.root.after(0, lambda: self.progress.start())
            self.root.after(0, lambda: self.progress_label.config(text="Downloading report..."))
            self.root.after(0, lambda: self.status_var.set("Downloading report..."))
            self.log(f"Downloading report for job: {self.job_id}", "INFO")
            
            try:
                url = self.url_var.get()
                response = requests.get(
                    f"{url}/api/v1/reports/{self.job_id}",
                    timeout=TIMEOUT
                )
                
                if response.status_code == 200:
                    self.report = response.json()
                    
                    # Save report
                    report_dir = Path("test_reports")
                    report_dir.mkdir(exist_ok=True)
                    report_file = report_dir / f"report_{self.job_id}.json"
                    
                    with open(report_file, 'w') as f:
                        json.dump(self.report, f, indent=2)
                    
                    self.log(f"✅ Report downloaded", "SUCCESS")
                    self.log(f"Saved to: {report_file}", "INFO")
                    self.status_var.set("✅ Report downloaded")
                    
                    # Display reports
                    self.display_report_summary()
                    self.display_full_report()
                    
                    # Mark visualizations as not generated (lazy load when tab is opened)
                    self.viz_generated = False
                    if not HAS_MATPLOTLIB:
                        self.log("⚠️ Matplotlib not available. Visualizations disabled.", "WARNING")
                    
                    # Update navigation buttons to reflect step 2 completion
                    # Refresh the current step display to enable Next button
                    if self.current_step == 2:
                        self.root.after(0, lambda: self.show_step(2))  # Refresh to enable Next button
                    
                    self.show_alert(
                        "Success",
                        f"Report downloaded successfully!\n\n"
                        f"Saved to: {report_file}\n\n"
                        f"You can now proceed to view the full report.",
                        'success'
                    )
                else:
                    self.log(f"❌ Download failed: {response.status_code}", "ERROR")
                    self.status_var.set("❌ Download failed")
                    self.show_alert("Error", f"Download failed: {response.status_code}", 'error')
            except Exception as e:
                self.log(f"❌ Error: {e}", "ERROR")
                self.root.after(0, lambda: self.status_var.set("❌ Error"))
                self.show_alert("Error", f"Download error: {e}", 'error')
            finally:
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.progress_label.config(text=""))
        
        threading.Thread(target=run_download, daemon=True).start()
    
    def display_report_summary(self):
        """Display beautifully formatted report summary in 2-column layout."""
        if not self.report:
            return
        
        # Clear both columns (enable editing temporarily)
        self.summary_text_left.config(state='normal')
        self.summary_text_right.config(state='normal')
        self.summary_text_left.delete(1.0, tk.END)
        self.summary_text_right.delete(1.0, tk.END)
        
        # Get data
        file_id = self.report.get('file_id', 'N/A')
        timestamp = self.report.get('timestamp', 'N/A')
        overall = self.report.get('overall_summary', {})
        summary = overall if overall else self.report.get('summary', {})
        
        total_segments = summary.get('total_segments', 0)
        risk_level = summary.get('overall_risk', summary.get('risk_level', 'N/A'))
        verification = summary.get('overall_verification_status', 'N/A')
        ai_prob = summary.get('overall_ai_probability', summary.get('ai_probability', 0))
        human_prob = 1.0 - ai_prob
        action = summary.get('recommended_action', 'N/A')
        flagged = summary.get('segments_flagged_ai', 0)
        matches = summary.get('segments_with_matches', 0)
        
        # ========== LEFT COLUMN ==========
        # File Information
        self.summary_text_left.insert(tk.END, "📋 File Information\n", "section")
        self.summary_text_left.insert(tk.END, "─" * 50 + "\n", "divider")
        self.summary_text_left.insert(tk.END, f"File ID: {file_id}\n", "info")
        self.summary_text_left.insert(tk.END, f"Timestamp: {timestamp}\n\n", "info")
        
        # Analysis Summary
        self.summary_text_left.insert(tk.END, "📊 Analysis Summary\n", "section")
        self.summary_text_left.insert(tk.END, "─" * 50 + "\n", "divider")
        self.summary_text_left.insert(tk.END, f"Total Segments Analyzed: {total_segments}\n", "info")
        self.summary_text_left.insert(tk.END, f"Risk Level: ", "info")
        self.summary_text_left.insert(tk.END, f"{risk_level.upper()}\n", "risk_" + risk_level.lower())
        self.summary_text_left.insert(tk.END, f"Verification Status: ", "info")
        self.summary_text_left.insert(tk.END, f"{verification.upper()}\n", "status_" + verification.lower())
        self.summary_text_left.insert(tk.END, f"AI Probability: ", "info")
        self.summary_text_left.insert(tk.END, f"{ai_prob:.1%}\n", "ai_prob")
        self.summary_text_left.insert(tk.END, f"Human Probability: ", "info")
        self.summary_text_left.insert(tk.END, f"{human_prob:.1%}\n", "human_prob")
        self.summary_text_left.insert(tk.END, f"Recommended Action: ", "info")
        self.summary_text_left.insert(tk.END, f"{action.replace('_', ' ').title()}\n", "action")
        self.summary_text_left.insert(tk.END, f"Segments Flagged as AI: {flagged}\n", "info")
        self.summary_text_left.insert(tk.END, f"Segments with Matches: {matches}\n", "info")
        
        # ========== RIGHT COLUMN ==========
        # Key Findings
        self.summary_text_right.insert(tk.END, "🔍 Key Findings\n", "section")
        self.summary_text_right.insert(tk.END, "─" * 50 + "\n", "divider")
        
        if ai_prob > 0.7:
            self.summary_text_right.insert(tk.END, "⚠️  HIGH AI PROBABILITY DETECTED\n", "warning")
            self.summary_text_right.insert(tk.END, "   This track shows strong indicators of AI-generated content.\n\n", "info")
        elif ai_prob > 0.5:
            self.summary_text_right.insert(tk.END, "⚡ MODERATE AI PROBABILITY\n", "warning")
            self.summary_text_right.insert(tk.END, "   This track may contain AI-generated elements.\n\n", "info")
        else:
            self.summary_text_right.insert(tk.END, "✅ LIKELY HUMAN-CREATED CONTENT\n", "success")
            self.summary_text_right.insert(tk.END, "   This track appears to be primarily human-created.\n\n", "info")
        
        if matches > 0:
            self.summary_text_right.insert(tk.END, f"🎯 {matches} segments matched known sources in database\n", "info")
            self.summary_text_right.insert(tk.END, "   Similar audio patterns were found in the reference library.\n\n", "info")
        else:
            self.summary_text_right.insert(tk.END, "🔍 No matches found in reference database\n", "info")
            self.summary_text_right.insert(tk.END, "   This track appears to be unique.\n\n", "info")
        
        # Stems Analysis
        stems_summary = self.report.get('stems_summary', [])
        if stems_summary:
            self.summary_text_right.insert(tk.END, "🎼 Stems Analysis\n", "section")
            self.summary_text_right.insert(tk.END, "─" * 50 + "\n", "divider")
            for stem_summary in stems_summary:
                stem_type = stem_summary.get('stem_type', 'unknown').capitalize()
                ai_score = stem_summary.get('aggregated_ai_score', 0.0)
                matches_count = stem_summary.get('matches_found', 0)
                risk = stem_summary.get('risk_flags', 'unknown')
                
                self.summary_text_right.insert(tk.END, f"{stem_type}:\n", "stem_type")
                self.summary_text_right.insert(tk.END, f"  • AI Score: {ai_score:.1%}\n", "info")
                self.summary_text_right.insert(tk.END, f"  • Matches: {matches_count}\n", "info")
                self.summary_text_right.insert(tk.END, f"  • Risk: {risk.upper()}\n\n", "info")
        
        # Configure text tags for colors (apply to both columns)
        for text_widget in [self.summary_text_left, self.summary_text_right]:
            text_widget.tag_config("section", font=('Segoe UI', 14, 'bold'), foreground=COLOR_ACCENT)
            text_widget.tag_config("divider", foreground=COLOR_BORDER)
            text_widget.tag_config("info", font=('Segoe UI', 11), foreground=COLOR_TEXT_SECONDARY)
            text_widget.tag_config("stem_type", font=('Segoe UI', 12, 'bold'), foreground=COLOR_TEXT_PRIMARY)
            text_widget.tag_config("success", font=('Segoe UI', 11, 'bold'), foreground=COLOR_SUCCESS)
            text_widget.tag_config("warning", font=('Segoe UI', 11, 'bold'), foreground=COLOR_WARNING)
            text_widget.tag_config("risk_low", foreground=COLOR_SUCCESS)
            text_widget.tag_config("risk_medium", foreground=COLOR_WARNING)
            text_widget.tag_config("risk_high", foreground=COLOR_ERROR)
            text_widget.tag_config("status_verified", foreground=COLOR_SUCCESS)
            text_widget.tag_config("status_suspicious", foreground=COLOR_WARNING)
            text_widget.tag_config("status_high_risk", foreground=COLOR_ERROR)
            text_widget.tag_config("ai_prob", foreground=COLOR_WARNING if ai_prob > 0.5 else COLOR_SUCCESS)
            text_widget.tag_config("human_prob", foreground=COLOR_SUCCESS if human_prob > 0.5 else COLOR_WARNING)
            text_widget.tag_config("action", foreground=COLOR_ACCENT)
    
    def display_full_report(self):
        """Display full JSON report with syntax highlighting (optimized)."""
        if not self.report:
            return
        
        # Batch text operations
        def update_report():
            self.details_text.delete(1.0, tk.END)
            formatted_json = json.dumps(self.report, indent=2)
            
            # Batch insert all text at once, then apply tags
            self.details_text.insert(1.0, formatted_json)
            
            # Apply syntax highlighting in batches
            lines = formatted_json.split('\n')
            start_line = 1
            for i, line in enumerate(lines):
                line_num = start_line + i
                if line.strip().startswith('"') and ':' in line:
                    if any(x in line for x in ['true', 'false', 'null']):
                        self.details_text.tag_add('json_value', f"{line_num}.0", f"{line_num}.end")
                    elif any(x in line for x in ['[', ']', '{', '}']):
                        self.details_text.tag_add('json_structure', f"{line_num}.0", f"{line_num}.end")
                    else:
                        self.details_text.tag_add('json_key', f"{line_num}.0", f"{line_num}.end")
                elif line.strip() in ['{', '}', '[', ']', '},', '{']:
                    self.details_text.tag_add('json_structure', f"{line_num}.0", f"{line_num}.end")
            
            # Configure JSON syntax colors (only once)
            if not hasattr(self, '_json_tags_configured'):
                self.details_text.tag_config('json_key', foreground='#60A5FA')
                self.details_text.tag_config('json_value', foreground='#10B981')
                self.details_text.tag_config('json_structure', foreground='#F59E0B')
                self._json_tags_configured = True
            
            self.details_text.see(1.0)
        
        # Execute in main thread
        self.root.after(0, update_report)
    
    def schedule_viz_generation(self):
        """Schedule visualization generation in background thread."""
        if self.viz_generated:
            return
        
        # Show loading indicator
        for widget in self.viz_container.winfo_children():
            widget.destroy()
        
        loading_label = tk.Label(
            self.viz_container,
            text="🔄 Generating visualizations...\n\nPlease wait...",
            bg=COLOR_BG_DARK,
            fg=COLOR_ACCENT,
            font=('Segoe UI', 14),
            justify=tk.CENTER
        )
        loading_label.pack(pady=100)
        
        # Generate in background thread
        threading.Thread(target=self._generate_visualizations_async, daemon=True).start()
    
    def _generate_visualizations_async(self):
        """Generate visualizations in background thread."""
        if not self.report:
            return
        
        if not HAS_MATPLOTLIB:
            self.root.after(0, lambda: self._show_no_matplotlib())
            return
        
        try:
            segments = self.report.get('segments', [])
            overall = self.report.get('overall_summary', {})
            
            if not segments:
                self.root.after(0, lambda: self._show_no_data())
                return
            
            # Extract data (fast operation)
            segment_times = []
            ai_probs = []
            fusion_scores = []
            risk_flags = []
            match_counts = []
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
                    match_counts.append(len(stem.get('matches', [])))
                    stem_types.append(stem.get('stem_type', 'unknown'))
                else:
                    ai_probs.append(seg.get('ai_probability', 0.0))
                    fusion_scores.append(0.0)
                    risk_flags.append(seg.get('risk_flag', 'low'))
                    match_counts.append(len(seg.get('matches', [])))
                    stem_types.append('unknown')
            
            # Clear container in main thread
            self.root.after(0, lambda: [w.destroy() for w in self.viz_container.winfo_children()])
            
            # Generate charts in a 2x2 grid layout
            # Use closures to capture values properly
            def create_charts():
                # Clear container
                for w in self.viz_container.winfo_children():
                    w.destroy()
                
                # Configure grid layout for 2x2 arrangement
                # Set equal weights so all cells expand to fill available space
                self.viz_container.grid_rowconfigure(0, weight=1)
                self.viz_container.grid_rowconfigure(1, weight=1)
                self.viz_container.grid_columnconfigure(0, weight=1)  # Expand to fill space
                self.viz_container.grid_columnconfigure(1, weight=1)  # Expand to fill space
                
                # Chart 1: Timeline (Top Left)
                self._update_viz_progress("Generating chart 1/4...")
                self.create_timeline_chart(
                    segment_times, ai_probs, fusion_scores,
                    "AI Probability & Fusion Score Timeline",
                    "Time (seconds)", "Probability",
                    grid_pos=(0, 0)  # Row 0, Column 0
                )
                
                # Chart 2: Risk Distribution (Top Right)
                self._update_viz_progress("Generating chart 2/4...")
                self.create_risk_distribution_chart(risk_flags, grid_pos=(0, 1))  # Row 0, Column 1
                
                # Chart 3: Stems Analysis (Bottom Left)
                self._update_viz_progress("Generating chart 3/4...")
                self.create_stems_analysis_chart(stem_types, ai_probs, grid_pos=(1, 0))  # Row 1, Column 0
                
                # Chart 4: Summary Pie Chart (Bottom Right)
                self._update_viz_progress("Generating chart 4/4...")
                self.create_summary_pie_chart(overall.get('overall_ai_probability', 0.0), grid_pos=(1, 1))  # Row 1, Column 1
                
                # Force update to ensure all charts are placed
                self.viz_container.update_idletasks()
                
                # Update canvas window to fill available space
                if hasattr(self, 'viz_canvas_window_id'):
                    # Get canvas width to fill the interface
                    self.viz_container.update_idletasks()
                    canvas_width = self.viz_canvas.winfo_width()
                    container_height = max(self.viz_container.winfo_reqheight(), 500)  # Minimum height for 2 rows
                    
                    # Use full canvas width to fill the interface (no extra space on right)
                    if canvas_width > 1:  # Canvas has been rendered
                        self.viz_canvas.itemconfig(
                            self.viz_canvas_window_id, 
                            width=canvas_width,  # Use full canvas width
                            height=container_height
                        )
                
                # Update canvas scroll region
                self.viz_canvas.update_idletasks()
                self.viz_canvas.configure(scrollregion=self.viz_canvas.bbox("all"))
                
                # Finalize
                self._finalize_viz()
            
            # Execute chart generation in main thread
            self.root.after(0, create_charts)
            
            # Final update
            self.root.after(0, lambda: self._finalize_viz())
            self.viz_generated = True
            
        except Exception as e:
            self.root.after(0, lambda e=e: self._show_viz_error(str(e)))
    
    def _update_viz_progress(self, message):
        """Update progress message for visualization generation."""
        try:
            for widget in self.viz_container.winfo_children():
                if isinstance(widget, tk.Label) and "Generating" in widget.cget("text"):
                    widget.config(text=message)
                    break
        except:
            pass  # Ignore errors if widget doesn't exist
    
    def _show_no_matplotlib(self):
        """Show message when matplotlib is not available."""
        for widget in self.viz_container.winfo_children():
            widget.destroy()
        
        no_viz_label = tk.Label(
            self.viz_container,
            text="⚠️ Matplotlib not available\n\nVisualizations require matplotlib to be installed.\n\n"
                 "Install with: pip install matplotlib",
            bg=COLOR_BG_DARK,
            fg=COLOR_WARNING,
            font=('Segoe UI', 14),
            justify=tk.CENTER
        )
        no_viz_label.pack(pady=100)
    
    def _show_no_data(self):
        """Show message when no data is available."""
        for widget in self.viz_container.winfo_children():
            widget.destroy()
        
        no_data_label = tk.Label(
            self.viz_container,
            text="No segment data available for visualization",
            bg=COLOR_BG_DARK,
            fg=COLOR_TEXT_SECONDARY,
            font=('Segoe UI', 12)
        )
        no_data_label.pack(pady=50)
    
    def _show_viz_error(self, error_msg):
        """Show error message for visualization generation."""
        for widget in self.viz_container.winfo_children():
            widget.destroy()
        
        error_label = tk.Label(
            self.viz_container,
            text=f"Error generating visualizations: {error_msg}",
            bg=COLOR_BG_DARK,
            fg=COLOR_ERROR,
            font=('Segoe UI', 12)
        )
        error_label.pack(pady=50)
    
    def _finalize_viz(self):
        """Finalize visualization generation."""
        self.viz_container.update_idletasks()
        self.viz_canvas.configure(scrollregion=self.viz_canvas.bbox("all"))
        self.log("✅ Visualizations generated successfully", "SUCCESS")
    
    def generate_visualizations(self):
        """Legacy method - redirects to lazy loading."""
        self.schedule_viz_generation()
        
        try:
            segments = self.report.get('segments', [])
            overall = self.report.get('overall_summary', {})
            
            if not segments:
                no_data_label = tk.Label(
                    self.viz_container,
                    text="No segment data available for visualization",
                    bg=COLOR_BG_DARK,
                    fg=COLOR_TEXT_SECONDARY,
                    font=('Segoe UI', 12)
                )
                no_data_label.pack(pady=50)
                return
            
            # Extract data for visualizations
            segment_times = []
            ai_probs = []
            fusion_scores = []
            risk_flags = []
            match_counts = []
            stem_types = []
            
            for seg in segments:
                start = seg.get('start', 0)
                end = seg.get('end', 0)
                segment_times.append((start + end) / 2)  # Midpoint
                
                stems = seg.get('stems', [])
                if stems:
                    stem = stems[0]  # Primary stem
                    classifier = stem.get('classifier', {})
                    ai_probs.append(classifier.get('ai_probability', 0.0))
                    fusion_scores.append(stem.get('fusion_score', 0.0))
                    risk_flags.append(seg.get('risk_flag', 'low'))
                    match_counts.append(len(stem.get('matches', [])))
                    stem_types.append(stem.get('stem_type', 'unknown'))
                else:
                    ai_probs.append(seg.get('ai_probability', 0.0))
                    fusion_scores.append(0.0)
                    risk_flags.append(seg.get('risk_flag', 'low'))
                    match_counts.append(len(seg.get('matches', [])))
                    stem_types.append('unknown')
            
            # Chart 1: AI Probability Timeline
            self.create_timeline_chart(
                segment_times, ai_probs, fusion_scores,
                "AI Probability & Fusion Score Timeline",
                "Time (seconds)",
                "Probability"
            )
            
            # Chart 2: Risk Level Distribution
            self.create_risk_distribution_chart(risk_flags)
            
            # Chart 3: Stems Analysis
            self.create_stems_analysis_chart(stem_types, ai_probs)
            
            # Chart 4: Match Statistics
            self.create_match_statistics_chart(match_counts, segment_times)
            
            # Chart 5: Overall Summary Pie Chart
            overall_ai_prob = overall.get('overall_ai_probability', 0.0)
            self.create_summary_pie_chart(overall_ai_prob)
            
            # Chart 6: Segment-by-Segment Bar Chart
            self.create_segment_bar_chart(segments[:20])  # First 20 segments
            
            # Update canvas scroll region
            self.viz_container.update_idletasks()
            self.viz_canvas.configure(scrollregion=self.viz_canvas.bbox("all"))
            
            self.log("✅ Visualizations generated successfully", "SUCCESS")
            
        except Exception as e:
            self.log(f"❌ Error generating visualizations: {e}", "ERROR")
            error_label = tk.Label(
                self.viz_container,
                text=f"Error generating visualizations: {e}",
                bg=COLOR_BG_DARK,
                fg=COLOR_ERROR,
                font=('Segoe UI', 12)
            )
            error_label.pack(pady=50)
    
    def create_timeline_chart(self, times, ai_probs, fusion_scores, title, xlabel, ylabel, grid_pos=None):
        """Create timeline chart showing AI probability and fusion scores."""
        # Reduced figure size for 2x2 grid layout - smaller to fit without scrolling
        fig = Figure(figsize=(4.5, 3), facecolor=COLOR_BG_DARK, dpi=70)
        ax = fig.add_subplot(111, facecolor=COLOR_BG_DARK)
        
        # Optimize markers - only show every Nth point for large datasets
        marker_step = max(1, len(times) // 50)  # Max 50 markers
        
        ax.plot(times, ai_probs, label='AI Probability', color=COLOR_WARNING, 
                linewidth=1.5, marker='o', markersize=3, markevery=marker_step, alpha=0.8)
        ax.plot(times, fusion_scores, label='Fusion Score', color=COLOR_ACCENT, 
                linewidth=1.5, marker='s', markersize=3, markevery=marker_step, alpha=0.8)
        ax.axhline(y=0.5, color=COLOR_ERROR, linestyle='--', alpha=0.5, label='AI Threshold (0.5)')
        
        ax.set_title(title, color=COLOR_TEXT_PRIMARY, fontsize=11, fontweight='bold', pad=10)
        ax.set_xlabel(xlabel, color=COLOR_TEXT_SECONDARY, fontsize=9)
        ax.set_ylabel(ylabel, color=COLOR_TEXT_SECONDARY, fontsize=9)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.2, color=COLOR_BORDER)
        ax.legend(loc='upper right', facecolor=COLOR_BG_CARD, edgecolor=COLOR_BORDER, 
                 labelcolor=COLOR_TEXT_PRIMARY)
        
        ax.tick_params(colors=COLOR_TEXT_SECONDARY)
        ax.spines['bottom'].set_color(COLOR_BORDER)
        ax.spines['top'].set_color(COLOR_BORDER)
        ax.spines['right'].set_color(COLOR_BORDER)
        ax.spines['left'].set_color(COLOR_BORDER)
        
        self.embed_chart(fig, grid_pos=grid_pos)
    
    def create_risk_distribution_chart(self, risk_flags, grid_pos=None):
        """Create pie chart showing risk level distribution."""
        risk_counts = {'low': 0, 'medium': 0, 'high': 0}
        for risk in risk_flags:
            risk_counts[risk.lower()] = risk_counts.get(risk.lower(), 0) + 1
        
        if sum(risk_counts.values()) == 0:
            return
        
        # Reduced figure size for 2x2 grid layout
        fig = Figure(figsize=(4.5, 3), facecolor=COLOR_BG_DARK, dpi=70)
        ax = fig.add_subplot(111, facecolor=COLOR_BG_DARK)
        
        labels = []
        sizes = []
        colors_list = []
        
        for risk, count in risk_counts.items():
            if count > 0:
                labels.append(risk.upper())
                sizes.append(count)
                if risk == 'low':
                    colors_list.append(COLOR_SUCCESS)
                elif risk == 'medium':
                    colors_list.append(COLOR_WARNING)
                else:
                    colors_list.append(COLOR_ERROR)
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors_list, autopct='%1.1f%%',
                                           textprops={'color': COLOR_TEXT_PRIMARY, 'fontsize': 10, 'fontweight': 'bold'})
        
        ax.set_title('Risk Level Distribution', color=COLOR_TEXT_PRIMARY, fontsize=11, fontweight='bold', pad=10)
        
        self.embed_chart(fig, grid_pos=grid_pos)
    
    def create_stems_analysis_chart(self, stem_types, ai_probs, grid_pos=None):
        """Create bar chart showing AI probability by stem type."""
        stem_data = {}
        for stem_type, ai_prob in zip(stem_types, ai_probs):
            if stem_type not in stem_data:
                stem_data[stem_type] = []
            stem_data[stem_type].append(ai_prob)
        
        stem_avg = {stem: np.mean(probs) if probs else 0.0 for stem, probs in stem_data.items()}
        
        if not stem_avg:
            return
        
        # Reduced figure size for 2x2 grid layout
        fig = Figure(figsize=(4.5, 3), facecolor=COLOR_BG_DARK, dpi=70)
        ax = fig.add_subplot(111, facecolor=COLOR_BG_DARK)
        
        stems = list(stem_avg.keys())
        avgs = list(stem_avg.values())
        colors = [COLOR_WARNING if avg > 0.5 else COLOR_SUCCESS for avg in avgs]
        
        bars = ax.bar(stems, avgs, color=colors, edgecolor=COLOR_BORDER, linewidth=1.5)
        ax.axhline(y=0.5, color=COLOR_ERROR, linestyle='--', alpha=0.5, label='AI Threshold')
        
        ax.set_title('Average AI Probability by Stem Type', color=COLOR_TEXT_PRIMARY, 
                    fontsize=11, fontweight='bold', pad=10)
        ax.set_xlabel('Stem Type', color=COLOR_TEXT_SECONDARY, fontsize=9)
        ax.set_ylabel('Average AI Probability', color=COLOR_TEXT_SECONDARY, fontsize=9)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.2, color=COLOR_BORDER, axis='y')
        ax.legend(facecolor=COLOR_BG_CARD, edgecolor=COLOR_BORDER, labelcolor=COLOR_TEXT_PRIMARY)
        
        ax.tick_params(colors=COLOR_TEXT_SECONDARY)
        ax.spines['bottom'].set_color(COLOR_BORDER)
        ax.spines['top'].set_color(COLOR_BORDER)
        ax.spines['right'].set_color(COLOR_BORDER)
        ax.spines['left'].set_color(COLOR_BORDER)
        
        # Add value labels on bars
        for bar, avg in zip(bars, avgs):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{avg:.2f}', ha='center', va='bottom', 
                   color=COLOR_TEXT_PRIMARY, fontweight='bold', fontsize=9)
        
        self.embed_chart(fig, grid_pos=grid_pos)
    
    def create_match_statistics_chart(self, match_counts, times):
        """Create chart showing match counts over time."""
        # Optimized figure size
        fig = Figure(figsize=(10, 4), facecolor=COLOR_BG_DARK, dpi=80)
        ax = fig.add_subplot(111, facecolor=COLOR_BG_DARK)
        
        ax.bar(times, match_counts, color=COLOR_ACCENT, alpha=0.7, edgecolor=COLOR_BORDER, width=0.3)
        
        ax.set_title('Matches Found per Segment', color=COLOR_TEXT_PRIMARY, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Time (seconds)', color=COLOR_TEXT_SECONDARY, fontsize=11)
        ax.set_ylabel('Number of Matches', color=COLOR_TEXT_SECONDARY, fontsize=11)
        ax.grid(True, alpha=0.2, color=COLOR_BORDER, axis='y')
        
        ax.tick_params(colors=COLOR_TEXT_SECONDARY)
        ax.spines['bottom'].set_color(COLOR_BORDER)
        ax.spines['top'].set_color(COLOR_BORDER)
        ax.spines['right'].set_color(COLOR_BORDER)
        ax.spines['left'].set_color(COLOR_BORDER)
        
        self.embed_chart(fig)
    
    def create_summary_pie_chart(self, overall_ai_prob, grid_pos=None):
        """Create pie chart showing overall AI vs Human probability."""
        # Reduced figure size for 2x2 grid layout - smaller to fit without scrolling
        fig = Figure(figsize=(4.5, 3), facecolor=COLOR_BG_DARK, dpi=70)
        ax = fig.add_subplot(111, facecolor=COLOR_BG_DARK)
        
        human_prob = 1.0 - overall_ai_prob
        sizes = [human_prob, overall_ai_prob]
        labels = ['Human', 'AI']
        colors = [COLOR_SUCCESS, COLOR_WARNING]
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                           textprops={'color': COLOR_TEXT_PRIMARY, 'fontsize': 10, 'fontweight': 'bold'},
                                           startangle=90)
        
        ax.set_title('Overall Content Classification', color=COLOR_TEXT_PRIMARY, 
                    fontsize=11, fontweight='bold', pad=10)
        
        self.embed_chart(fig, grid_pos=grid_pos)
    
    def create_segment_bar_chart(self, segments):
        """Create bar chart showing AI probability for each segment."""
        if not segments:
            return
        
        segment_ids = [f"Seg {i+1}" for i in range(len(segments))]
        ai_probs = []
        
        for seg in segments:
            stems = seg.get('stems', [])
            if stems:
                classifier = stems[0].get('classifier', {})
                ai_probs.append(classifier.get('ai_probability', 0.0))
            else:
                ai_probs.append(seg.get('ai_probability', 0.0))
        
        # Optimized figure size - limit to 20 segments max
        max_segments = min(20, len(segments))
        segment_ids = segment_ids[:max_segments]
        ai_probs = ai_probs[:max_segments]
        
        fig = Figure(figsize=(12, 5), facecolor=COLOR_BG_DARK, dpi=80)
        ax = fig.add_subplot(111, facecolor=COLOR_BG_DARK)
        
        colors = [COLOR_WARNING if p > 0.5 else COLOR_SUCCESS for p in ai_probs]
        bars = ax.bar(range(len(segment_ids)), ai_probs, color=colors, edgecolor=COLOR_BORDER, linewidth=1)
        ax.axhline(y=0.5, color=COLOR_ERROR, linestyle='--', alpha=0.5, label='AI Threshold')
        
        ax.set_title('AI Probability by Segment (First 20 Segments)', 
                    color=COLOR_TEXT_PRIMARY, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Segment', color=COLOR_TEXT_SECONDARY, fontsize=11)
        ax.set_ylabel('AI Probability', color=COLOR_TEXT_SECONDARY, fontsize=11)
        ax.set_xticks(range(len(segment_ids)))
        ax.set_xticklabels(segment_ids, rotation=45, ha='right')
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.2, color=COLOR_BORDER, axis='y')
        ax.legend(facecolor=COLOR_BG_CARD, edgecolor=COLOR_BORDER, labelcolor=COLOR_TEXT_PRIMARY)
        
        ax.tick_params(colors=COLOR_TEXT_SECONDARY)
        ax.spines['bottom'].set_color(COLOR_BORDER)
        ax.spines['top'].set_color(COLOR_BORDER)
        ax.spines['right'].set_color(COLOR_BORDER)
        ax.spines['left'].set_color(COLOR_BORDER)
        
        self.embed_chart(fig)
    
    def embed_chart(self, fig, grid_pos=None):
        """Embed a matplotlib figure into the visualization container."""
        # Create a frame for the chart - reduced padding to fit without scrolling
        chart_frame = tk.Frame(self.viz_container, bg=COLOR_BG_DARK, padx=2, pady=2)
        
        # Use grid layout if position is specified, otherwise use pack (for backward compatibility)
        if grid_pos is not None:
            row, col = grid_pos
            chart_frame.grid(row=row, column=col, sticky=(tk.W, tk.E, tk.N, tk.S), padx=2, pady=2)
            # Configure the chart frame to expand
            chart_frame.grid_rowconfigure(0, weight=1)
            chart_frame.grid_columnconfigure(0, weight=1)
            
            # Create canvas and embed figure directly (no toolbar)
            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Store canvas reference for potential updates
            chart_frame._canvas = canvas
        else:
            chart_frame.pack(fill=tk.BOTH, expand=True)
            
            # Create canvas and embed figure (no toolbar)
            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


def main():
    """Run the Beatlibrary Provenance application."""
    root = tk.Tk()
    app = BeatlibraryProvenanceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
