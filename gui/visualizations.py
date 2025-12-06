"""Visualization components for displaying provenance report charts."""
import numpy as np
from typing import List, Optional, Tuple
from .constants import (
    COLOR_BG_DARK, COLOR_BG_CARD, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_ACCENT, COLOR_BORDER, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR
)

# Matplotlib imports with fallback
HAS_MATPLOTLIB = False
try:
    import matplotlib
    matplotlib.use('TkAgg', force=False)
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class ChartGenerator:
    """Generates matplotlib charts for provenance reports."""
    
    def __init__(self, container, canvas=None, canvas_window_id=None):
        """
        Initialize chart generator.
        
        Args:
            container: Tkinter frame to embed charts in
            canvas: Optional canvas for scrollable container
            canvas_window_id: Optional canvas window ID for resizing
        """
        self.container = container
        self.canvas = canvas
        self.canvas_window_id = canvas_window_id
    
    def create_timeline_chart(
        self,
        times: List[float],
        ai_probs: List[float],
        fusion_scores: List[float],
        title: str,
        xlabel: str,
        ylabel: str,
        grid_pos: Optional[Tuple[int, int]] = None
    ):
        """Create timeline chart showing AI probability and fusion scores."""
        if not HAS_MATPLOTLIB:
            return
        
        fig = Figure(figsize=(4.5, 3), facecolor=COLOR_BG_DARK, dpi=70)
        ax = fig.add_subplot(111, facecolor=COLOR_BG_DARK)
        
        marker_step = max(1, len(times) // 50)
        
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
        for spine in ax.spines.values():
            spine.set_color(COLOR_BORDER)
        
        self._embed_chart(fig, grid_pos)
    
    def create_risk_distribution_chart(
        self,
        risk_flags: List[str],
        grid_pos: Optional[Tuple[int, int]] = None
    ):
        """Create pie chart showing risk level distribution."""
        if not HAS_MATPLOTLIB:
            return
        
        risk_counts = {'low': 0, 'medium': 0, 'high': 0}
        for risk in risk_flags:
            risk_counts[risk.lower()] = risk_counts.get(risk.lower(), 0) + 1
        
        if sum(risk_counts.values()) == 0:
            return
        
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
        
        ax.pie(sizes, labels=labels, colors=colors_list, autopct='%1.1f%%',
               textprops={'color': COLOR_TEXT_PRIMARY, 'fontsize': 10, 'fontweight': 'bold'})
        
        ax.set_title('Risk Level Distribution', color=COLOR_TEXT_PRIMARY,
                    fontsize=11, fontweight='bold', pad=10)
        
        self._embed_chart(fig, grid_pos)
    
    def create_stems_analysis_chart(
        self,
        stem_types: List[str],
        ai_probs: List[float],
        grid_pos: Optional[Tuple[int, int]] = None
    ):
        """Create bar chart showing AI probability by stem type."""
        if not HAS_MATPLOTLIB:
            return
        
        stem_data = {}
        for stem_type, ai_prob in zip(stem_types, ai_probs):
            if stem_type not in stem_data:
                stem_data[stem_type] = []
            stem_data[stem_type].append(ai_prob)
        
        stem_avg = {stem: np.mean(probs) if probs else 0.0 for stem, probs in stem_data.items()}
        
        if not stem_avg:
            return
        
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
        for spine in ax.spines.values():
            spine.set_color(COLOR_BORDER)
        
        # Add value labels on bars
        for bar, avg in zip(bars, avgs):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{avg:.2f}', ha='center', va='bottom',
                   color=COLOR_TEXT_PRIMARY, fontweight='bold', fontsize=9)
        
        self._embed_chart(fig, grid_pos)
    
    def create_summary_pie_chart(
        self,
        overall_ai_prob: float,
        grid_pos: Optional[Tuple[int, int]] = None
    ):
        """Create pie chart showing overall AI vs Human probability."""
        if not HAS_MATPLOTLIB:
            return
        
        fig = Figure(figsize=(4.5, 3), facecolor=COLOR_BG_DARK, dpi=70)
        ax = fig.add_subplot(111, facecolor=COLOR_BG_DARK)
        
        human_prob = 1.0 - overall_ai_prob
        sizes = [human_prob, overall_ai_prob]
        labels = ['Human', 'AI']
        colors = [COLOR_SUCCESS, COLOR_WARNING]
        
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
               textprops={'color': COLOR_TEXT_PRIMARY, 'fontsize': 10, 'fontweight': 'bold'},
               startangle=90)
        
        ax.set_title('Overall Content Classification', color=COLOR_TEXT_PRIMARY,
                    fontsize=11, fontweight='bold', pad=10)
        
        self._embed_chart(fig, grid_pos)
    
    def _embed_chart(self, fig: Figure, grid_pos: Optional[Tuple[int, int]] = None):
        """Embed a matplotlib figure into the container."""
        import tkinter as tk
        
        chart_frame = tk.Frame(self.container, bg=COLOR_BG_DARK, padx=2, pady=2)
        
        if grid_pos is not None:
            row, col = grid_pos
            chart_frame.grid(row=row, column=col, sticky=(tk.W, tk.E, tk.N, tk.S), padx=2, pady=2)
            chart_frame.grid_rowconfigure(0, weight=1)
            chart_frame.grid_columnconfigure(0, weight=1)
            
            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            chart_frame._canvas = canvas
        else:
            chart_frame.pack(fill=tk.BOTH, expand=True)
            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

