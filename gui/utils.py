"""Utility functions for the GUI application."""
import tkinter as tk
import time
from typing import Optional
from .constants import (
    COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_TEXT_SECONDARY
)


class Logger:
    """Thread-safe logger for GUI application."""
    
    def __init__(self, log_text_widget: tk.Text, root: tk.Tk):
        """
        Initialize logger.
        
        Args:
            log_text_widget: Tkinter Text widget for log output
            root: Root Tkinter window for thread-safe updates
        """
        self.log_text = log_text_widget
        self.root = root
        self._tags_configured = set()
    
    def log(self, message: str, level: str = "INFO"):
        """
        Add color-coded message to log (thread-safe).
        
        Args:
            message: Log message
            level: Log level (INFO, SUCCESS, WARNING, ERROR)
        """
        timestamp = time.strftime("%H:%M:%S")
        color_map = {
            "INFO": "#60A5FA",
            "SUCCESS": COLOR_SUCCESS,
            "WARNING": COLOR_WARNING,
            "ERROR": COLOR_ERROR
        }
        color = color_map.get(level, COLOR_TEXT_SECONDARY)
        
        def update_log():
            self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
            self.log_text.insert(tk.END, f"[{level}] ", level.lower())
            self.log_text.insert(tk.END, f"{message}\n")
            
            # Configure tags (only once per level)
            if "timestamp" not in self._tags_configured:
                self.log_text.tag_config("timestamp", foreground="#666666")
                self._tags_configured.add("timestamp")
            
            if level.lower() not in self._tags_configured:
                self.log_text.tag_config(level.lower(), foreground=color,
                                       font=('Consolas', 10, 'bold'))
                self._tags_configured.add(level.lower())
            
            # Only scroll if near the end
            if self.log_text.index(tk.END).split('.')[0] == self.log_text.index('end-1c').split('.')[0]:
                self.log_text.see(tk.END)
        
        # Use after() for thread-safe updates
        self.root.after(0, update_log)


def apply_dark_title_bar(root: tk.Tk):
    """Apply dark/black title bar and rounded corners (Windows-specific)."""
    import platform
    
    # Only apply on Windows
    if platform.system() != 'Windows':
        return
    
    try:
        import ctypes
        
        # Get window handle
        try:
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
            if hwnd == 0:
                hwnd = root.winfo_id()
        except:
            hwnd = root.winfo_id()
        
        # Windows 10/11: Use DWM to enable dark mode title bar
        try:
            dwmapi = ctypes.windll.dwmapi
            
            # Enable dark mode title bar (black)
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(1)
            
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value),
                ctypes.sizeof(value)
            )
            
            # Set rounded corners (Windows 11+)
            try:
                DWMWA_WINDOW_CORNER_PREFERENCE = 33
                corner_preference = ctypes.c_int(2)  # DWMWCP_ROUND
                
                dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    DWMWA_WINDOW_CORNER_PREFERENCE,
                    ctypes.byref(corner_preference),
                    ctypes.sizeof(corner_preference)
                )
            except Exception:
                pass  # Rounded corners not supported
                
        except Exception:
            pass
    except Exception:
        pass


def set_window_icon(root: tk.Tk, icon_path: Optional[str] = None):
    """
    Set window icon with cross-platform support (Windows/Mac).
    
    Args:
        root: Root Tkinter window
        icon_path: Path to icon file
    """
    try:
        from pathlib import Path
        import sys
        import platform
        
        system = platform.system()
        
        if icon_path is None:
            # Try to find icon file in multiple locations
            possible_paths = []
            
            # Determine icon extension based on platform
            icon_ext = '.icns' if system == 'Darwin' else '.ico'
            
            # 1. If running from PyInstaller bundle, look in bundle directory
            if hasattr(sys, '_MEIPASS'):
                bundle_dir = Path(sys._MEIPASS)
                possible_paths.append(bundle_dir / f"icon{icon_ext}")
                possible_paths.append(bundle_dir / "icon.ico")  # Fallback
                possible_paths.append(bundle_dir / "icon.icns")  # Fallback
                # Also try in root of bundle
                if bundle_dir.parent:
                    possible_paths.append(bundle_dir.parent / f"icon{icon_ext}")
                    possible_paths.append(bundle_dir.parent / "icon.ico")
                    possible_paths.append(bundle_dir.parent / "icon.icns")
            
            # 2. Try next to the executable (for bundled exe/app)
            if hasattr(sys, 'executable') and sys.executable:
                exe_dir = Path(sys.executable).parent
                possible_paths.append(exe_dir / f"icon{icon_ext}")
                possible_paths.append(exe_dir / "icon.ico")  # Fallback
                possible_paths.append(exe_dir / "icon.icns")  # Fallback
                # For macOS .app bundles, also check Contents/Resources
                if system == 'Darwin' and exe_dir.name == 'MacOS':
                    resources_dir = exe_dir.parent.parent / "Resources"
                    possible_paths.append(resources_dir / f"icon{icon_ext}")
                    possible_paths.append(resources_dir / "icon.ico")
                    possible_paths.append(resources_dir / "icon.icns")
            
            # 3. Try in project directory (for development)
            script_dir = Path(__file__).parent.parent.absolute()
            possible_paths.append(script_dir / f"icon{icon_ext}")
            possible_paths.append(script_dir / "icon.ico")  # Fallback
            possible_paths.append(script_dir / "icon.icns")  # Fallback
            
            # 4. Try current working directory
            possible_paths.append(Path.cwd() / f"icon{icon_ext}")
            possible_paths.append(Path.cwd() / "icon.ico")  # Fallback
            possible_paths.append(Path.cwd() / "icon.icns")  # Fallback
            
            # Find first existing icon file
            icon_path = None
            for path in possible_paths:
                if path and Path(path).exists():
                    icon_path = str(path)
                    break
        
        # Platform-specific icon handling
        if system == 'Windows':
            # Windows-specific icon handling
        try:
            import ctypes
            
            # Get window handle
            try:
                hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
                if hwnd == 0:
                    hwnd = root.winfo_id()
            except:
                hwnd = root.winfo_id()
            
            # Load icon using Windows API
            IMAGE_ICON = 1
            LR_LOADFROMFILE = 0x0010
            LR_DEFAULTSIZE = 0x0040
            
            hicon_small = 0
            hicon_large = 0
            
                # Try to load from file path first
            if icon_path and Path(icon_path).exists():
                try:
                    # Set icon using iconbitmap (for titlebar)
                    root.iconbitmap(icon_path)
                except Exception:
                    pass
                
                    # Load icon using Windows API (only works with .ico files)
                    if icon_path.lower().endswith('.ico'):
                abs_path_wide = ctypes.create_unicode_buffer(icon_path)
                hicon_small = ctypes.windll.user32.LoadImageW(
                    0, abs_path_wide, IMAGE_ICON, 16, 16, LR_LOADFROMFILE
                )
                hicon_large = ctypes.windll.user32.LoadImageW(
                    0, abs_path_wide, IMAGE_ICON, 32, 32, LR_LOADFROMFILE
                )
            
            # If loading from file failed or file not found, try loading from EXE (embedded icon)
            if not hicon_small or not hicon_large:
                if hasattr(sys, 'executable') and sys.executable and Path(sys.executable).exists():
                    exe_path_wide = ctypes.create_unicode_buffer(sys.executable)
                    hicon_small = ctypes.windll.user32.LoadImageW(
                        0, exe_path_wide, IMAGE_ICON, 16, 16, LR_LOADFROMFILE | LR_DEFAULTSIZE
                    )
                    hicon_large = ctypes.windll.user32.LoadImageW(
                        0, exe_path_wide, IMAGE_ICON, 32, 32, LR_LOADFROMFILE | LR_DEFAULTSIZE
                    )
                    if hicon_small or hicon_large:
                        icon_path = sys.executable
            
            # Set icons
            if hicon_small or hicon_large:
                WM_SETICON = 0x0080
                ICON_SMALL = 0
                ICON_BIG = 1
                
                if hicon_small:
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
                if hicon_large:
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_large)
            except Exception:
                pass
        
        elif system == 'Darwin':  # macOS
            # macOS icon handling
            if icon_path and Path(icon_path).exists():
                try:
                    # On macOS, use iconbitmap with .icns file (preferred) or .ico
                    root.iconbitmap(icon_path)
                except Exception:
                    # Fallback: try the other format
                    if icon_path.endswith('.icns'):
                        ico_path = icon_path.replace('.icns', '.ico')
                        if Path(ico_path).exists():
                            try:
                                root.iconbitmap(ico_path)
                                icon_path = ico_path
                            except Exception:
                                pass
                    elif icon_path.endswith('.ico'):
                        icns_path = icon_path.replace('.ico', '.icns')
                        if Path(icns_path).exists():
                            try:
                                root.iconbitmap(icns_path)
                                icon_path = icns_path
                            except Exception:
                                pass
        
        else:  # Linux and other platforms
            # Linux/Unix icon handling
            if icon_path and Path(icon_path).exists():
                try:
                    root.iconbitmap(icon_path)
        except Exception:
            pass
        
        return icon_path if icon_path else None
    except Exception:
        return None

