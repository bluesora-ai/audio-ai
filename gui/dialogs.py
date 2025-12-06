"""Custom dialog components for the GUI application."""
import tkinter as tk
from .constants import (
    COLOR_BG_DARK, COLOR_BG_CARD, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR
)


class CustomAlert:
    """Custom dark-themed alert dialog matching the app design."""
    
    def __init__(self, parent, title, message, alert_type='info'):
        self.parent = parent
        self.result = None
        
        # Create top-level window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        
        # Calculate approximate height based on message length
        message_lines = max(3, len(message) // 60)
        estimated_height = max(280, 50 + 40 + 50 + (message_lines * 25))
        self.dialog.geometry(f"450x{estimated_height}")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=COLOR_BG_DARK)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog on parent window
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (450 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (estimated_height // 2)
        self.dialog.geometry(f"450x{estimated_height}+{x}+{y}")
        
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
        
        # Content area
        content_frame = tk.Frame(container, bg=COLOR_BG_DARK)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # Message text
        message_text = tk.Text(
            content_frame,
            bg=COLOR_BG_DARK,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 11),
            wrap=tk.WORD,
            width=45,
            height=max(3, message.count('\n') + 1),
            relief=tk.FLAT,
            bd=0,
            padx=0,
            pady=0,
            highlightthickness=0,
            insertwidth=0
        )
        message_text.insert('1.0', message)
        message_text.config(state=tk.DISABLED)
        message_text.pack(anchor=tk.W, fill=tk.BOTH, expand=True, pady=(0, 20))
        
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
        
        # Calculate approximate height based on message length
        message_lines = max(3, len(message) // 60)
        estimated_height = max(280, 50 + 40 + 50 + (message_lines * 25))
        self.dialog.geometry(f"450x{estimated_height}")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=COLOR_BG_DARK)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (450 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (estimated_height // 2)
        self.dialog.geometry(f"450x{estimated_height}+{x}+{y}")
        
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
        
        # Content
        content_frame = tk.Frame(container, bg=COLOR_BG_DARK)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # Message text
        message_text = tk.Text(
            content_frame,
            bg=COLOR_BG_DARK,
            fg=COLOR_TEXT_PRIMARY,
            font=('Segoe UI', 11),
            wrap=tk.WORD,
            width=45,
            height=max(3, message.count('\n') + 1),
            relief=tk.FLAT,
            bd=0,
            padx=0,
            pady=0,
            highlightthickness=0,
            insertwidth=0
        )
        message_text.insert('1.0', message)
        message_text.config(state=tk.DISABLED)
        message_text.pack(anchor=tk.W, fill=tk.BOTH, expand=True, pady=(0, 20))
        
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

