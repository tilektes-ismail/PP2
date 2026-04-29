# ============================================================
#  persistence.py  —  TSIS 3
#  Handles leaderboard and settings read/write (JSON files).
# ============================================================

import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))

LEADERBOARD_FILE = os.path.join(_HERE, "leaderboard.json")
SETTINGS_FILE    = os.path.join(_HERE, "settings.json")

# ---- Default settings --------------------------------------------------------
DEFAULT_SETTINGS = {
    "sound":      True,
    "car_color":  "blue",     # blue | red | yellow
    "difficulty": "normal",   # easy | normal | hard
}

# ---- Leaderboard -------------------------------------------------------------

def load_leaderboard() -> list:
    """Return list of dicts: [{name, score, distance, coins}, …] sorted desc."""
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    try:
        with open(LEADERBOARD_FILE, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, IOError):
        pass
    return []


def save_leaderboard(entries: list):
    """Persist the leaderboard list to disk (keeps top 10)."""
    entries = sorted(entries, key=lambda e: e.get("score", 0), reverse=True)[:10]
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def add_entry(name: str, score: int, distance: int, coins: int):
    """Append a new run result and re-save, returning the updated list."""
    entries = load_leaderboard()
    entries.append({
        "name":     name,
        "score":    score,
        "distance": distance,
        "coins":    coins,
    })
    save_leaderboard(entries)
    return load_leaderboard()


# ---- Settings ----------------------------------------------------------------

def load_settings() -> dict:
    """Return settings dict (falls back to defaults for missing keys)."""
    settings = dict(DEFAULT_SETTINGS)
    if not os.path.exists(SETTINGS_FILE):
        return settings
    try:
        with open(SETTINGS_FILE, "r") as f:
            saved = json.load(f)
        settings.update({k: v for k, v in saved.items() if k in DEFAULT_SETTINGS})
    except (json.JSONDecodeError, IOError):
        pass
    return settings


def save_settings(settings: dict):
    """Write settings dict to disk."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)
