"""Entry point for the GUI application."""
import sys
import os
import traceback
from pathlib import Path

def setup_logging():
    """Setup error logging to file for debugging."""
    log_dir = Path.home() / "Library" / "Logs" / "AudioProvenanceGUI"
    if sys.platform != 'darwin':
        # For non-macOS, use a local logs directory
        log_dir = Path(__file__).parent / "logs"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "error.log"
    
    def log_exception(exc_type, exc_value, exc_traceback):
        """Log unhandled exceptions to file."""
        if exc_type == KeyboardInterrupt:
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                from datetime import datetime
                f.write(f"\n{'='*80}\n")
                f.write(f"Error at {datetime.now().isoformat()}\n")
                f.write(f"{'='*80}\n")
                f.write(error_msg)
                f.write(f"\n{'='*80}\n\n")
        except Exception:
            pass  # Can't log if logging fails
    
    sys.excepthook = log_exception
    return log_file

def main():
    """Main entry point with error handling."""
    log_file = setup_logging()
    
    try:
        from gui.main import main as gui_main
        gui_main()
    except Exception as e:
        # Log the error
        error_msg = f"Fatal error during startup:\n{traceback.format_exc()}"
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                from datetime import datetime
                f.write(f"\n{'='*80}\n")
                f.write(f"Startup error at {datetime.now().isoformat()}\n")
                f.write(f"{'='*80}\n")
                f.write(error_msg)
                f.write(f"\n{'='*80}\n\n")
        except Exception:
            pass
        
        # Try to show error dialog if possible
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()  # Hide main window
            messagebox.showerror(
                "Application Error",
                f"An error occurred while starting the application.\n\n"
                f"Error: {str(e)}\n\n"
                f"Please check the log file for details:\n{log_file}"
            )
            root.destroy()
        except Exception:
            pass
        
        sys.exit(1)

if __name__ == "__main__":
    main()

