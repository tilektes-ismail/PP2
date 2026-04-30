# Snake Game — TSIS 4

Extended Snake game with PostgreSQL leaderboard, power-ups, poison food, obstacles, settings persistence, and polished game screens.

## Requirements

```
pip install pygame psycopg2-binary
```

## Database Setup (optional)

If you have PostgreSQL running, create the database and set environment variables:

```bash
createdb snake_game

export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=snake_game
export DB_USER=postgres
export DB_PASS=postgres
```

The game runs perfectly **without** a database — scores just won't be persisted.

Tables are auto-created on first run:

```sql
CREATE TABLE players (
    id       SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE game_sessions (
    id            SERIAL PRIMARY KEY,
    player_id     INTEGER REFERENCES players(id),
    score         INTEGER   NOT NULL,
    level_reached INTEGER   NOT NULL,
    played_at     TIMESTAMP DEFAULT NOW()
);
```

## Run

```bash
python main.py
```

## Features

| Feature | Details |
|---|---|
| **Leaderboard** | Top 10 all-time scores from PostgreSQL |
| **Personal Best** | Shown during gameplay (HUD top-left) |
| **Weighted Food** | Red (1×), Blue (3×, 10 s), Gold (5×, 5 s) |
| **Poison Food** | Dark red — shortens snake by 2; game over if too short |
| **Power-ups** | Speed boost (orange), Slow motion (cyan), Shield (purple) — each lasts 5 s; disappears from field after 8 s |
| **Obstacles** | Random wall blocks added from Level 3 onward |
| **Settings** | Grid toggle, sound toggle, snake color — saved to `settings.json` |
| **Screens** | Main Menu, Game, Game Over, Leaderboard, Settings |

## Controls

| Key | Action |
|---|---|
| Arrow keys | Move snake |
| ESC | Return to main menu |
| Q | Quit (on game over screen) |

## Project Structure

```
TSIS4/
├── main.py         # Entry point + all game screens
├── game.py         # Core game loop
├── entities.py     # Snake, Food, PoisonFood, PowerUp, Obstacle
├── db.py           # PostgreSQL integration (psycopg2)
├── settings.py     # Load/save settings.json
├── config.py       # Constants, colors, DB config
└── settings.json   # User preferences (auto-created)
```
