"""
db.py — Database layer using psycopg2.
Handles connection, schema creation, saving sessions, and leaderboard queries.
Falls back gracefully when DB is unavailable (so the game still runs offline).
"""

import datetime

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

_conn = None  # module-level singleton connection


def get_connection():
    global _conn
    if not PSYCOPG2_AVAILABLE:
        return None
    try:
        if _conn is None or _conn.closed:
            _conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                connect_timeout=3,
            )
        return _conn
    except Exception as e:
        print(f"[DB] Connection failed: {e}")
        return None


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    if conn is None:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id       SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS game_sessions (
                    id            SERIAL PRIMARY KEY,
                    player_id     INTEGER REFERENCES players(id),
                    score         INTEGER   NOT NULL,
                    level_reached INTEGER   NOT NULL,
                    played_at     TIMESTAMP DEFAULT NOW()
                );
            """)
        conn.commit()
        return True
    except Exception as e:
        print(f"[DB] init_db error: {e}")
        conn.rollback()
        return False


def get_or_create_player(username: str) -> int | None:
    """Return player id, creating the row if needed."""
    conn = get_connection()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO players (username) VALUES (%s) ON CONFLICT (username) DO NOTHING;",
                (username,),
            )
            cur.execute("SELECT id FROM players WHERE username = %s;", (username,))
            row = cur.fetchone()
        conn.commit()
        return row[0] if row else None
    except Exception as e:
        print(f"[DB] get_or_create_player error: {e}")
        conn.rollback()
        return None


def save_session(player_id: int, score: int, level: int):
    conn = get_connection()
    if conn is None:
        return
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO game_sessions (player_id, score, level_reached) VALUES (%s, %s, %s);",
                (player_id, score, level),
            )
        conn.commit()
    except Exception as e:
        print(f"[DB] save_session error: {e}")
        conn.rollback()


def get_personal_best(player_id: int) -> int:
    conn = get_connection()
    if conn is None:
        return 0
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(score), 0) FROM game_sessions WHERE player_id = %s;",
                (player_id,),
            )
            row = cur.fetchone()
        return row[0] if row else 0
    except Exception as e:
        print(f"[DB] get_personal_best error: {e}")
        return 0


def get_leaderboard(limit: int = 10):
    """Return list of (rank, username, score, level, played_at)."""
    conn = get_connection()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.username, gs.score, gs.level_reached, gs.played_at
                FROM game_sessions gs
                JOIN players p ON p.id = gs.player_id
                ORDER BY gs.score DESC
                LIMIT %s;
            """, (limit,))
            rows = cur.fetchall()
        return [
            (i + 1, row[0], row[1], row[2], row[3].strftime("%Y-%m-%d") if row[3] else "")
            for i, row in enumerate(rows)
        ]
    except Exception as e:
        print(f"[DB] get_leaderboard error: {e}")
        return []
