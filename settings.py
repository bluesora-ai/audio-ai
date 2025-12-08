# settings.py - DMG build configuration for dmgbuild
import os

# Path to the built .app bundle
app_path = os.path.abspath("dist/AudioProvenanceGUI.app")

# Volume name shown when mounted
volume_name = "AudioProvenanceGUI"

# Files to include in the DMG
files = [app_path]

# DMG format (UDZO = compressed read-only)
format = "UDZO"

