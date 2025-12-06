"""Constants and configuration for the GUI application."""
# API Configuration
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

# Window Configuration
WINDOW_TITLE = "Beatlibrary - Audio Provenance"
WINDOW_SIZE = "1400x950"
WINDOW_MIN_SIZE = (1200, 700)

# Step Names
STEP_NAMES = ["Connection & Upload", "Processing", "Report"]

