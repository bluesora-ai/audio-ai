"""Theme configuration and styling for the GUI application."""
import tkinter as tk
from tkinter import ttk
from .constants import (
    COLOR_BG_DARK, COLOR_BG_CARD, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_BORDER, COLOR_INPUT_BG
)


def setup_dark_theme():
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
                   padding=[20, 10],
                   borderwidth=0,
                   focuscolor='none',
                   font=('Segoe UI', 10))
    # Map selected state - keep same padding and font to prevent size change
    style.map('TNotebook.Tab',
             background=[('selected', COLOR_ACCENT)],
             foreground=[('selected', COLOR_TEXT_PRIMARY)],
             padding=[('selected', [20, 10]), ('!selected', [20, 10])],
             font=[('selected', ('Segoe UI', 10)), ('!selected', ('Segoe UI', 10))])
    
    style.configure('TProgressbar',
                   background=COLOR_ACCENT,
                   troughcolor=COLOR_BG_CARD,
                   borderwidth=0,
                   lightcolor=COLOR_ACCENT,
                   darkcolor=COLOR_ACCENT)


def create_card(parent, padx=0, pady=0):
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


def create_button(parent, text, command, style='primary', width=None):
    """Create a styled button."""
    from .constants import COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_BG_CARD, COLOR_BG_HOVER, COLOR_TEXT_PRIMARY
    
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

