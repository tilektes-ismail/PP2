# ============================================================
#  persistence.py  —  TSIS 3
#  Handles leaderboard and settings read/write (JSON files).
# ============================================================
# This entire file is responsible for saving and loading data to/from disk.
# It uses JSON files so the data survives between game sessions.
# There are two kinds of data managed here:
#   1. Leaderboard — a list of past run results (name, score, distance, coins)
#   2. Settings    — user preferences (sound on/off, car color, difficulty)

import json
# json — Python's built-in library for reading and writing JSON files.
# JSON (JavaScript Object Notation) is a simple text format for storing structured data.
# Example JSON: {"name": "Alice", "score": 420}

import os
# os — used to build file paths and check whether files exist on disk.

_HERE = os.path.dirname(os.path.abspath(__file__))
# __file__            — the path to THIS script (persistence.py).
# os.path.abspath()   — converts it to a full absolute path.
# os.path.dirname()   — strips the filename, leaving just the folder.
# Result: _HERE = the folder where persistence.py lives (same folder as main.py).
# Used below so all file paths work regardless of where the game is launched from.

LEADERBOARD_FILE = os.path.join(_HERE, "leaderboard.json")
# Builds the full path to the leaderboard file, e.g.:
# "C:/projects/cardodge/leaderboard.json"
# os.path.join() handles slashes correctly on Windows (\) and Mac/Linux (/).

SETTINGS_FILE    = os.path.join(_HERE, "settings.json")
# Same idea — full path to the settings file, e.g.:
# "C:/projects/cardodge/settings.json"

# ---- Default settings --------------------------------------------------------
DEFAULT_SETTINGS = {
    "sound":      True,       # Sound is ON by default
    "car_color":  "blue",     # blue | red | yellow — the player's car color
    "difficulty": "normal",   # easy | normal | hard — the selected difficulty
}
# This dict acts as a fallback.
# If settings.json doesn't exist yet (first launch), these values are used.
# If settings.json exists but is missing a key (e.g. a new setting was added
# in a later version), the default fills in the gap — prevents crashes.

# ---- Leaderboard -------------------------------------------------------------

def load_leaderboard() -> list:
    """Return list of dicts: [{name, score, distance, coins}, …] sorted desc."""
    # Reads leaderboard.json from disk and returns its contents as a Python list.
    # Each item in the list is a dict representing one completed run.
    # Returns an empty list [] if the file doesn't exist or is corrupted.
    # The "-> list" annotation is just a hint telling readers what type is returned.

    if not os.path.exists(LEADERBOARD_FILE):
        # If leaderboard.json doesn't exist yet (e.g. first time ever launching),
        # there's nothing to load — return an empty list immediately.
        return []

    try:
        # try/except wraps the file reading so a corrupted file doesn't crash the game.
        with open(LEADERBOARD_FILE, "r") as f:
            # Open the file in read mode ("r").
            # `with` ensures the file is automatically closed when the block ends,
            # even if an error occurs inside.
            data = json.load(f)
            # json.load() parses the entire JSON file into a Python object.
            # A valid leaderboard file should produce a list of dicts here.

        if isinstance(data, list):
            # Sanity check: make sure what we got is actually a list.
            # If the file was manually edited and contains something else
            # (like a dict or a number), we skip it and return [] below.
            return data
            # Return the valid leaderboard list to the caller.

    except (json.JSONDecodeError, IOError):
        # json.JSONDecodeError — the file exists but contains invalid JSON text.
        # IOError             — the file couldn't be read (permissions, locked, etc.).
        # In both cases, silently ignore the error and fall through to return [].
        pass

    return []
    # Reached if: the file was unreadable, invalid JSON, or data wasn't a list.
    # Returning an empty list is the safest fallback — the game simply starts
    # with no leaderboard history rather than crashing.


def save_leaderboard(entries: list):
    """Persist the leaderboard list to disk (keeps top 10)."""
    # Takes a list of run-result dicts and writes them to leaderboard.json.
    # Automatically sorts by score (highest first) and trims to the top 10.

    entries = sorted(entries, key=lambda e: e.get("score", 0), reverse=True)[:10]
    # sorted() returns a NEW sorted list (doesn't modify `entries` in place).
    # key=lambda e: e.get("score", 0)
    #   — for each entry dict `e`, extract the "score" value to sort by.
    #   — .get("score", 0) returns 0 if the "score" key is missing (safe fallback).
    # reverse=True — sort descending: highest score first.
    # [:10] — slice: keep only the first 10 entries after sorting.
    #   If there are fewer than 10, all of them are kept.

    with open(LEADERBOARD_FILE, "w") as f:
        # Open (or create) leaderboard.json in write mode ("w").
        # "w" overwrites the entire file from scratch each time.
        json.dump(entries, f, indent=2)
        # json.dump() converts the Python list to JSON text and writes it to the file.
        # indent=2 makes the output human-readable with 2-space indentation, e.g.:
        # [
        #   {
        #     "name": "Alice",
        #     "score": 420
        #   }
        # ]


def add_entry(name: str, score: int, distance: int, coins: int):
    """Append a new run result and re-save, returning the updated list."""
    # Called at the end of every game (crash or quit) to record the player's result.
    # Loads the current leaderboard, appends the new entry, saves it, and returns
    # the freshly updated leaderboard (already sorted and trimmed to top 10).

    entries = load_leaderboard()
    # Load whatever is currently saved on disk (may be an empty list on first run).

    entries.append({
        "name":     name,      # Player's username (entered at start of game)
        "score":    score,     # Final combined score (enemy score + coins + distance)
        "distance": distance,  # Raw distance counter (frames survived)
        "coins":    coins,     # Total coins collected this run
    })
    # Append a new dict representing this completed run to the list.
    # .append() modifies `entries` in place, adding the dict at the end.

    save_leaderboard(entries)
    # Write the updated list back to disk.
    # save_leaderboard() also handles sorting and trimming to top 10.

    return load_leaderboard()
    # Read the file back from disk and return the final sorted list.
    # This double-read (save then load) guarantees the returned list
    # exactly matches what's on disk — no discrepancies from in-memory sorting.


# ---- Settings ----------------------------------------------------------------

def load_settings() -> dict:
    """Return settings dict (falls back to defaults for missing keys)."""
    # Reads settings.json and returns a dict of user preferences.
    # Always returns a complete dict — missing or broken keys are filled
    # in from DEFAULT_SETTINGS so the rest of the game never gets a KeyError.

    settings = dict(DEFAULT_SETTINGS)
    # Start with a COPY of the defaults (dict() creates a shallow copy).
    # If nothing else succeeds below, these defaults will be returned.
    # We copy — not reference — so modifications to `settings` don't
    # accidentally mutate the module-level DEFAULT_SETTINGS dict.

    if not os.path.exists(SETTINGS_FILE):
        # settings.json doesn't exist yet (first launch or file was deleted).
        # Return the defaults immediately — no point trying to open a missing file.
        return settings

    try:
        with open(SETTINGS_FILE, "r") as f:
            # Open settings.json in read mode.
            saved = json.load(f)
            # Parse the JSON into a Python dict, stored in `saved`.

        settings.update({k: v for k, v in saved.items() if k in DEFAULT_SETTINGS})
        # dict comprehension: {k: v for k, v in saved.items() if k in DEFAULT_SETTINGS}
        #   — iterate over every key-value pair in the saved file.
        #   — only keep pairs whose key exists in DEFAULT_SETTINGS.
        #   — this filters out any unknown/obsolete keys (e.g. from an old game version).
        # settings.update(...) merges those filtered pairs INTO `settings`,
        # overwriting the defaults with the player's actual saved preferences.
        # Keys present in DEFAULT_SETTINGS but missing from the file are untouched,
        # so they keep their default values — safe for newly added settings.

    except (json.JSONDecodeError, IOError):
        # File is corrupted or unreadable — silently ignore and return the defaults.
        pass

    return settings
    # Return the fully merged settings dict.
    # It always contains every key from DEFAULT_SETTINGS, with values from
    # the saved file where available and defaults everywhere else.


def save_settings(settings: dict):
    """Write settings dict to disk."""
    # Saves the current settings dict to settings.json.
    # Called when the player changes a setting or quits the game.

    with open(SETTINGS_FILE, "w") as f:
        # Open (or create) settings.json in write mode — overwrites previous content.
        json.dump(settings, f, indent=2)
        # Serialize the dict to formatted JSON and write it.
        # indent=2 keeps the file readable if someone opens it in a text editor.
        # Example output:
        # {
        #   "sound": true,
        #   "car_color": "red",
        #   "difficulty": "hard"
        # }