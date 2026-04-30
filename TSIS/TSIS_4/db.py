"""
db.py — Database layer using psycopg2.
Handles connection, schema creation, saving sessions, and leaderboard queries.
Falls back gracefully when DB is unavailable (so the game still runs offline).
"""
# This file is the database access layer — it's the ONLY place in the entire
# project that talks directly to PostgreSQL. Every other module that needs
# database data calls a function from here instead of writing SQL itself.
# The key design goal: if the database is missing or broken, the game still runs.
# Every function checks for a valid connection first and returns a safe default
# (None, 0, [], or False) if anything goes wrong.

import datetime
# datetime — used in get_leaderboard() to format the played_at timestamp
# from a Python datetime object into a human-readable "YYYY-MM-DD" string.

try:
    import psycopg2
    # psycopg2 — the most popular PostgreSQL adapter for Python.
    # It lets us open connections, run SQL queries, and fetch results.
    import psycopg2.extras
    # psycopg2.extras — optional extension module with convenience features
    # (e.g. DictCursor, execute_values). Imported here for availability
    # even though this file currently uses only the base cursor.
    PSYCOPG2_AVAILABLE = True
    # Flag: psycopg2 is installed and importable on this machine.
except ImportError:
    # psycopg2 is NOT installed (e.g. a player running the game without a DB setup).
    # Instead of crashing the entire game at startup, we catch the ImportError
    # and set the flag to False. Every function below checks this flag first.
    PSYCOPG2_AVAILABLE = False

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
# Import the five PostgreSQL connection parameters from config.py.
# Keeping credentials in a separate config file means:
#   1. You never accidentally commit passwords to version control.
#   2. Changing the DB server only requires editing one file.
# DB_HOST — hostname or IP of the PostgreSQL server, e.g. "localhost"
# DB_PORT — port number, typically 5432 for PostgreSQL
# DB_NAME — the database name to connect to
# DB_USER — the PostgreSQL username
# DB_PASS — the password for that user

_conn = None  # module-level singleton connection
# This module-level variable holds the single shared database connection.
# "Singleton" means only ONE connection object is ever created per program run.
# All functions reuse this same connection instead of opening a new one each time,
# which is much more efficient (opening a DB connection has overhead).
# The leading underscore _ signals "private — only use inside this module".
# Starts as None because no connection has been made yet at import time.


def get_connection():
    # Returns the active database connection, creating it if needed.
    # This is called at the start of every other function in this file.
    # If the connection can't be established, returns None — callers must handle this.

    global _conn
    # Declare that we want to read AND write the module-level _conn variable.
    # Without `global`, Python would treat `_conn = ...` as creating a new local variable.

    if not PSYCOPG2_AVAILABLE:
        # psycopg2 isn't installed — can't connect to any database.
        return None
        # Return None immediately. The game will run in offline mode.

    try:
        if _conn is None or _conn.closed:
            # _conn is None   → first call ever, no connection made yet.
            # _conn.closed    → connection existed but was closed (DB restart, network drop).
            #   .closed is a psycopg2 property: 0 = open, non-zero = closed.
            # In either case, we need to create a fresh connection.
            _conn = psycopg2.connect(
                host=DB_HOST,         # Server address
                port=DB_PORT,         # Server port
                dbname=DB_NAME,       # Which database to use
                user=DB_USER,         # Login username
                password=DB_PASS,     # Login password
                connect_timeout=3,    # Give up after 3 seconds if the server doesn't respond.
                                      # Without this, the game could freeze for 30+ seconds
                                      # trying to reach an unreachable server.
            )
        return _conn
        # Return the existing open connection (or the one we just created).

    except Exception as e:
        # Catches any connection error: wrong password, server not running,
        # network unreachable, timeout, etc.
        print(f"[DB] Connection failed: {e}")
        # Print a diagnostic message so developers can see what went wrong.
        # The [DB] prefix makes it easy to spot database messages in the console.
        return None
        # Signal to the caller that no connection is available.


def init_db():
    """Create tables if they don't exist."""
    # Called once at game startup to ensure the database schema exists.
    # Uses "CREATE TABLE IF NOT EXISTS" so it's safe to call every time —
    # if the tables already exist, nothing changes.
    # Returns True on success, False if the DB is unavailable or errored.

    conn = get_connection()
    if conn is None:
        return False
        # No DB connection available — skip silently, game runs without DB.

    try:
        with conn.cursor() as cur:
            # Open a cursor — the object used to send SQL commands to the database.
            # `with` ensures the cursor is closed automatically when the block ends.

            cur.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id       SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL
                );
            """)
            # Create the `players` table if it doesn't already exist.
            # id:       SERIAL       — auto-incrementing integer assigned by the DB (1, 2, 3, ...).
            # id:       PRIMARY KEY  — uniquely identifies each row; indexed automatically.
            # username: VARCHAR(50)  — text column, max 50 characters.
            # username: UNIQUE       — no two players can have the same username.
            # username: NOT NULL     — a player row must have a username.

            cur.execute("""
                CREATE TABLE IF NOT EXISTS game_sessions (
                    id            SERIAL PRIMARY KEY,
                    player_id     INTEGER REFERENCES players(id),
                    score         INTEGER   NOT NULL,
                    level_reached INTEGER   NOT NULL,
                    played_at     TIMESTAMP DEFAULT NOW()
                );
            """)
            # Create the `game_sessions` table — one row per completed game run.
            # id:            SERIAL PRIMARY KEY — unique auto-increment ID for each session.
            # player_id:     INTEGER REFERENCES players(id) — foreign key linking this session
            #                to the player who played it. If the player row is deleted,
            #                the DB enforces referential integrity.
            # score:         INTEGER NOT NULL — the final score; must always be provided.
            # level_reached: INTEGER NOT NULL — how far the player got; must always be provided.
            # played_at:     TIMESTAMP DEFAULT NOW() — when the game was played.
            #                DEFAULT NOW() means the DB automatically fills in the current
            #                timestamp if we don't provide one (which we don't in save_session).

        conn.commit()
        # Commit the transaction — make the CREATE TABLE changes permanent on disk.
        # Without commit(), the changes exist only in memory and are lost if the
        # program crashes or the connection closes.
        return True
        # Signal success to the caller.

    except Exception as e:
        print(f"[DB] init_db error: {e}")
        conn.rollback()
        # Undo any partial changes from this transaction.
        # Important after an error: leaves the DB in a clean, consistent state
        # rather than a half-applied state.
        return False


def get_or_create_player(username: str) -> int | None:
    """Return player id, creating the row if needed."""
    # Looks up the player by username. If they don't exist yet, creates them first.
    # Returns the player's integer ID (from the `players` table), or None on failure.
    # The "int | None" return type annotation means "returns either an int or None".

    conn = get_connection()
    if conn is None:
        return None
        # No DB available — return None. Callers check for None before using the ID.

    try:
        with conn.cursor() as cur:

            cur.execute(
                "INSERT INTO players (username) VALUES (%s) ON CONFLICT (username) DO NOTHING;",
                (username,),
            )
            # Try to insert a new player row with this username.
            # %s is a parameter placeholder — psycopg2 safely substitutes `username` here,
            # preventing SQL injection (never use f-strings or + for SQL values).
            # ON CONFLICT (username) DO NOTHING:
            #   If a player with this username already exists (UNIQUE constraint),
            #   don't raise an error — just skip the insert silently.
            # Result: after this line, the player row definitely exists.

            cur.execute("SELECT id FROM players WHERE username = %s;", (username,))
            # Now fetch the player's ID. Works whether we just inserted or it already existed.

            row = cur.fetchone()
            # fetchone() returns the first result row as a tuple, e.g. (42,), or None if no match.

        conn.commit()
        # Commit the INSERT (if one happened). The SELECT doesn't need committing,
        # but we commit here to finalize any writes.

        return row[0] if row else None
        # row[0] extracts the `id` integer from the tuple (42,).
        # If row is None (shouldn't happen, but defensive), return None.

    except Exception as e:
        print(f"[DB] get_or_create_player error: {e}")
        conn.rollback()
        # Undo the failed INSERT to keep the DB clean.
        return None


def save_session(player_id: int, score: int, level: int):
    # Records one completed game run in the `game_sessions` table.
    # Called at game over with the player's ID, final score, and highest level reached.
    # Returns nothing — if it fails, we log the error but don't crash the game.

    conn = get_connection()
    if conn is None:
        return
        # No DB — silently skip saving. The local leaderboard.json still works.

    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO game_sessions (player_id, score, level_reached) VALUES (%s, %s, %s);",
                (player_id, score, level),
            )
            # Insert a new row with the three values.
            # played_at is omitted — the DB fills it automatically with NOW() (current timestamp).
            # %s placeholders prevent SQL injection.

        conn.commit()
        # Persist the new session row to disk.

    except Exception as e:
        print(f"[DB] save_session error: {e}")
        conn.rollback()
        # Roll back the failed INSERT.


def get_personal_best(player_id: int) -> int:
    # Returns the highest score this player has ever achieved, or 0 if none.
    # Used to show "Personal Best: X" on the HUD or game-over screen.

    conn = get_connection()
    if conn is None:
        return 0
        # No DB — return 0 as a safe default (no known personal best).

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(score), 0) FROM game_sessions WHERE player_id = %s;",
                (player_id,),
            )
            # MAX(score) — finds the highest score value in all rows for this player.
            # COALESCE(MAX(score), 0) — if the player has no sessions yet, MAX() returns NULL.
            #   COALESCE() replaces NULL with 0, so we always get an integer back.
            # WHERE player_id = %s — filters to only THIS player's sessions.

            row = cur.fetchone()
            # Returns something like (420,) — a one-element tuple with the max score.

        return row[0] if row else 0
        # Extract the integer from the tuple, or return 0 if fetchone() returned None.
        # (fetchone() returning None here would be unusual given COALESCE, but defensive.)

    except Exception as e:
        print(f"[DB] get_personal_best error: {e}")
        return 0
        # On any error, return 0 — the game continues without a personal best display.
        # No rollback needed here because SELECT doesn't modify data.


def get_leaderboard(limit: int = 10):
    """Return list of (rank, username, score, level, played_at)."""
    # Fetches the top `limit` game sessions by score, with the player's username joined in.
    # Returns a list of tuples ready to display in the leaderboard screen.
    # Default limit=10 — shows top 10 entries unless the caller requests more/fewer.

    conn = get_connection()
    if conn is None:
        return []
        # No DB — return an empty list. The UI will show "No entries yet."

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.username, gs.score, gs.level_reached, gs.played_at
                FROM game_sessions gs
                JOIN players p ON p.id = gs.player_id
                ORDER BY gs.score DESC
                LIMIT %s;
            """, (limit,))
            # SELECT — choose four columns to return:
            #   p.username    — the player's name (from the players table)
            #   gs.score      — the run's final score
            #   gs.level_reached — how far they got
            #   gs.played_at  — when they played (a Python datetime object after fetching)
            #
            # FROM game_sessions gs — query the sessions table, aliased as "gs" for brevity.
            #
            # JOIN players p ON p.id = gs.player_id — link each session to its player.
            #   This is an INNER JOIN: only sessions with a matching player row are included.
            #   Aliased as "p" for brevity.
            #
            # ORDER BY gs.score DESC — highest scores first (descending order).
            #
            # LIMIT %s — return at most `limit` rows (default 10).
            #   Using a parameter prevents injection even for numeric values.

            rows = cur.fetchall()
            # fetchall() returns ALL result rows as a list of tuples, e.g.:
            # [("Alice", 900, 7, datetime(2025, 4, 1, ...)),
            #  ("Bob",   750, 5, datetime(2025, 3, 28, ...)), ...]

        return [
            (i + 1, row[0], row[1], row[2], row[3].strftime("%Y-%m-%d") if row[3] else "")
            for i, row in enumerate(rows)
        ]
        # Transform the raw DB rows into a cleaner list of tuples for the UI.
        # List comprehension iterates over rows with enumerate() to get the index i.
        # For each row, build a 5-element tuple:
        #   i + 1       — rank (1-based: 1st place, 2nd place, etc.)
        #   row[0]      — username string, e.g. "Alice"
        #   row[1]      — score integer, e.g. 900
        #   row[2]      — level_reached integer, e.g. 7
        #   row[3].strftime("%Y-%m-%d") if row[3] else ""
        #               — format the played_at datetime as "2025-04-01",
        #                 or an empty string if it's NULL in the DB.
        # Result example: [(1, "Alice", 900, 7, "2025-04-01"), (2, "Bob", 750, 5, "2025-03-28")]

    except Exception as e:
        print(f"[DB] get_leaderboard error: {e}")
        return []
        # On any error, return an empty list — the leaderboard screen handles this gracefully.