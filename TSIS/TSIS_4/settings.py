"""
settings.py — Load/save user preferences from settings.json.
This module is the only place that reads from or writes to the settings file,
keeping all file I/O for preferences in one spot.
"""

# json: used to serialize the settings dict to a human-readable .json file and read it back
import json
# os: used to build a file path that works on any OS and to check if the file exists
import os

# Build the full absolute path to settings.json, placing it in the same directory
# as this script (__file__). os.path.dirname(__file__) gives that directory,
# and os.path.join() assembles it with the filename in an OS-safe way.
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

# Default values used when no settings file exists yet, or when a key is missing
# from an older settings file (e.g. after a new setting is added in an update).
DEFAULTS = {
    "snake_color": [255, 255, 255],  # white snake — stored as a list because JSON has no tuple type
    "grid_overlay": True,            # show the grid lines overlay by default
    "sound": False,                  # sound is off by default
}


def load_settings() -> dict:
    # Only try to read the file if it actually exists on disk.
    if os.path.exists(SETTINGS_FILE):
        try:
            # Open the file in read mode and parse its JSON content into a Python dict.
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)

            # Start with a fresh copy of DEFAULTS so every expected key is present.
            # Then overwrite with whatever keys were found in the saved file.
            # This "merge" pattern means: if the file is missing a new key (added in a
            # later version), the default value is used instead of crashing.
            merged = dict(DEFAULTS)
            merged.update(data)
            return merged

        except Exception as e:
            # If the file is corrupted or unreadable for any reason, log the error
            # and fall through to returning defaults below — never crash the game.
            print(f"[Settings] Load failed: {e}")

    # File doesn't exist (first launch) or loading failed — return a fresh copy of defaults.
    # dict(DEFAULTS) makes a shallow copy so callers can't accidentally mutate the original.
    return dict(DEFAULTS)


def save_settings(settings: dict):
    try:
        # Open (or create) the settings file in write mode, overwriting any existing content.
        with open(SETTINGS_FILE, "w") as f:
            # Serialize the dict to JSON. indent=2 makes the file human-readable
            # with 2-space indentation, so it's easy to inspect or edit manually.
            json.dump(settings, f, indent=2)

    except Exception as e:
        # If the write fails (e.g. no disk space, permission denied), log it and
        # continue — a failed save is annoying but shouldn't crash the game.
        print(f"[Settings] Save failed: {e}")