"""
settings.py — Load/save user preferences from settings.json.
"""

import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULTS = {
    "snake_color": [255, 255, 255],  # RGB
    "grid_overlay": True,
    "sound": False,
}


def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            # Merge with defaults so new keys are always present
            merged = dict(DEFAULTS)
            merged.update(data)
            return merged
        except Exception as e:
            print(f"[Settings] Load failed: {e}")
    return dict(DEFAULTS)


def save_settings(settings: dict):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"[Settings] Save failed: {e}")
