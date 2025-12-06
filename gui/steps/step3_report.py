"""Step 3: Report Display component."""
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Optional, Dict
from ..constants import (
    COLOR_BG_DARK, COLOR_BG_CARD, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_ACCENT
)
from ..theme import create_card


class Step3Report:
    """Step 3 component: Report display with tabs."""
    
    def __init__(self, parent: tk.Frame):
        """
        Initialize Step 3 component.
        
        Args:
            parent: Parent frame
        """
        self.parent = parent
        self.frame = None
        self.notebook = None
        self.summary_text_left = None
        self.summary_text_right = None
        self.details_text = None
        self.log_text = None
        self.viz_container = None
        self.viz_canvas = None
        self.viz_canvas_window_id = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Create Step 3 UI."""
        self.frame = tk.Frame(self.parent, bg=COLOR_BG_DARK)
        step3_card = create_card(self.frame)
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
        self.notebook = ttk.Notebook(step3_inner)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Summary tab
        self._create_summary_tab()
        
        # Details tab
        self._create_details_tab()
        
        # Visualizations tab
        self._create_visualizations_tab()
        
        # Logs tab
        self._create_logs_tab()
    
    def _create_summary_tab(self):
        """Create summary tab with 2-column layout."""
        summary_frame = tk.Frame(self.notebook, bg=COLOR_BG_CARD)
        self.notebook.add(summary_frame, text="  Summary  ")
        
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
            state='disabled'
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
            state='disabled'
        )
        right_text.pack(fill=tk.BOTH, expand=True)
        self.summary_text_right = right_text
    
    def _create_details_tab(self):
        """Create full report details tab."""
        details_frame = tk.Frame(self.notebook, bg=COLOR_BG_CARD)
        self.notebook.add(details_frame, text="  Full Report  ")
        
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
    
    def _create_visualizations_tab(self):
        """Create visualizations tab."""
        viz_frame = tk.Frame(self.notebook, bg=COLOR_BG_CARD)
        self.notebook.add(viz_frame, text="  📊 Visualizations  ")
        
        # Scrollable canvas for visualizations
        viz_canvas = tk.Canvas(viz_frame, bg=COLOR_BG_DARK, highlightthickness=0)
        viz_scrollbar = ttk.Scrollbar(viz_frame, orient="vertical", command=viz_canvas.yview)
        viz_scrollable = tk.Frame(viz_canvas, bg=COLOR_BG_DARK)
        
        def update_scroll_region(event):
            viz_canvas.configure(scrollregion=viz_canvas.bbox("all"))
        
        viz_scrollable.bind("<Configure>", update_scroll_region)
        
        canvas_window_id = viz_canvas.create_window((0, 0), window=viz_scrollable, anchor="nw")
        viz_canvas.configure(yscrollcommand=viz_scrollbar.set)
        
        def on_canvas_configure(event):
            canvas_width = event.width
            try:
                current_height = viz_canvas.itemcget(canvas_window_id, 'height')
                if current_height and current_height != '':
                    viz_canvas.itemconfig(canvas_window_id, width=canvas_width, height=current_height)
                else:
                    viz_canvas.itemconfig(canvas_window_id, width=canvas_width)
            except:
                viz_canvas.itemconfig(canvas_window_id, width=canvas_width)
        
        viz_canvas.bind('<Configure>', on_canvas_configure)
        
        self.viz_canvas_window_id = canvas_window_id
        self.viz_canvas = viz_canvas
        self.viz_container = viz_scrollable
        
        viz_canvas.pack(side="left", fill="both", expand=True)
        viz_scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel
        def on_viz_mousewheel(event):
            viz_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        viz_canvas.bind_all("<MouseWheel>", on_viz_mousewheel)
    
    def _create_logs_tab(self):
        """Create processing logs tab."""
        logs_frame = tk.Frame(self.notebook, bg=COLOR_BG_CARD)
        self.notebook.add(logs_frame, text="  Processing Logs  ")
        
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
    
    def bind_tab_change(self, callback):
        """Bind callback for tab change events."""
        def on_tab_changed(event):
            selected = event.widget.tab('current')['text'].strip()
            callback(selected)
        
        self.notebook.bind('<<NotebookTabChanged>>', on_tab_changed)

