"""Report display utilities for formatting and showing provenance reports."""
import tkinter as tk
import json
from typing import Dict, Optional
from .constants import (
    COLOR_BG_DARK, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_ACCENT,
    COLOR_BORDER, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR
)


class ReportDisplayer:
    """Handles display of provenance reports in various formats."""
    
    def __init__(self, summary_text_left: tk.Text, summary_text_right: tk.Text,
                 details_text: tk.Text):
        """
        Initialize report displayer.
        
        Args:
            summary_text_left: Left column text widget for summary
            summary_text_right: Right column text widget for summary
            details_text: Text widget for full JSON report
        """
        self.summary_text_left = summary_text_left
        self.summary_text_right = summary_text_right
        self.details_text = details_text
        self._json_tags_configured = False
    
    def display_summary(self, report: Dict):
        """
        Display report summary in 2-column layout.
        
        Args:
            report: Provenance report dictionary
        """
        # Clear both columns
        self.summary_text_left.config(state='normal')
        self.summary_text_right.config(state='normal')
        self.summary_text_left.delete(1.0, tk.END)
        self.summary_text_right.delete(1.0, tk.END)
        
        # Get data
        file_id = report.get('file_id', 'N/A')
        timestamp = report.get('created_at', report.get('timestamp', 'N/A'))
        overall = report.get('overall_summary', {})
        summary = overall if overall else report.get('summary', {})
        
        total_segments = summary.get('total_segments', 0)
        risk_level = summary.get('overall_risk', summary.get('risk_level', 'N/A'))
        verification = summary.get('overall_verification_status', 'N/A')
        ai_prob = summary.get('overall_ai_probability', summary.get('ai_probability', 0))
        human_prob = 1.0 - ai_prob
        action = summary.get('recommended_action', 'N/A')
        flagged = summary.get('segments_flagged_ai', 0)
        matches = summary.get('segments_with_matches', 0)
        
        # Left column: File Information & Analysis Summary
        self.summary_text_left.insert(tk.END, "📋 File Information\n", "section")
        self.summary_text_left.insert(tk.END, "─" * 50 + "\n", "divider")
        self.summary_text_left.insert(tk.END, f"File ID: {file_id}\n", "info")
        self.summary_text_left.insert(tk.END, f"Timestamp: {timestamp}\n\n", "info")
        
        self.summary_text_left.insert(tk.END, "📊 Analysis Summary\n", "section")
        self.summary_text_left.insert(tk.END, "─" * 50 + "\n", "divider")
        self.summary_text_left.insert(tk.END, f"Total Segments Analyzed: {total_segments}\n", "info")
        self.summary_text_left.insert(tk.END, f"Risk Level: ", "info")
        self.summary_text_left.insert(tk.END, f"{risk_level.upper()}\n", f"risk_{risk_level.lower()}")
        self.summary_text_left.insert(tk.END, f"Verification Status: ", "info")
        self.summary_text_left.insert(tk.END, f"{verification.upper()}\n", f"status_{verification.lower()}")
        self.summary_text_left.insert(tk.END, f"AI Probability: ", "info")
        self.summary_text_left.insert(tk.END, f"{ai_prob:.1%}\n", "ai_prob")
        self.summary_text_left.insert(tk.END, f"Human Probability: ", "info")
        self.summary_text_left.insert(tk.END, f"{human_prob:.1%}\n", "human_prob")
        self.summary_text_left.insert(tk.END, f"Recommended Action: ", "info")
        self.summary_text_left.insert(tk.END, f"{action.replace('_', ' ').title()}\n", "action")
        self.summary_text_left.insert(tk.END, f"Segments Flagged as AI: {flagged}\n", "info")
        self.summary_text_left.insert(tk.END, f"Segments with Matches: {matches}\n", "info")
        
        # Right column: Key Findings & Stems Analysis
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
        stems_summary = report.get('stems_summary', [])
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
        
        # Configure text tags
        self._configure_summary_tags(ai_prob, human_prob)
        
        # Make read-only
        self.summary_text_left.config(state='disabled')
        self.summary_text_right.config(state='disabled')
    
    def display_full_report(self, report: Dict):
        """
        Display full JSON report with syntax highlighting.
        
        Args:
            report: Provenance report dictionary
        """
        def update_report():
            self.details_text.delete(1.0, tk.END)
            formatted_json = json.dumps(report, indent=2)
            
            self.details_text.insert(1.0, formatted_json)
            
            # Apply syntax highlighting
            lines = formatted_json.split('\n')
            for i, line in enumerate(lines, start=1):
                if line.strip().startswith('"') and ':' in line:
                    if any(x in line for x in ['true', 'false', 'null']):
                        self.details_text.tag_add('json_value', f"{i}.0", f"{i}.end")
                    elif any(x in line for x in ['[', ']', '{', '}']):
                        self.details_text.tag_add('json_structure', f"{i}.0", f"{i}.end")
                    else:
                        self.details_text.tag_add('json_key', f"{i}.0", f"{i}.end")
                elif line.strip() in ['{', '}', '[', ']', '},', '{']:
                    self.details_text.tag_add('json_structure', f"{i}.0", f"{i}.end")
            
            # Configure JSON syntax colors
            if not self._json_tags_configured:
                self.details_text.tag_config('json_key', foreground='#60A5FA')
                self.details_text.tag_config('json_value', foreground='#10B981')
                self.details_text.tag_config('json_structure', foreground='#F59E0B')
                self._json_tags_configured = True
            
            self.details_text.see(1.0)
        
        # Execute in main thread
        self.details_text.after(0, update_report)
    
    def _configure_summary_tags(self, ai_prob: float, human_prob: float):
        """Configure text tags for summary display."""
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

