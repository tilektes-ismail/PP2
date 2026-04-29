import os

# Screen
CELL = 10
SCREEN_WIDTH, SCREEN_HEIGHT = 400, 400

# Directions
UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3

# Colors
BLACK       = (0, 0, 0)
WHITE       = (255, 255, 255)
GRAY        = (30, 30, 30)
DARK_GRAY   = (50, 50, 50)
RED         = (220, 50, 50)
GREEN       = (50, 200, 50)
BLUE        = (50, 100, 220)
GOLD        = (255, 215, 0)
DARK_RED    = (139, 0, 0)
CYAN        = (0, 220, 220)
ORANGE      = (255, 140, 0)
PURPLE      = (160, 32, 240)

# Game
FOOD_PER_LEVEL = 3
INITIAL_SPEED  = 5

# Screens
SCREEN_MENU       = "menu"
SCREEN_GAME       = "game"
SCREEN_GAMEOVER   = "gameover"
SCREEN_LEADERBOARD = "leaderboard"
SCREEN_SETTINGS   = "settings"

# DB (override with env vars)
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "snake_game")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "postgres")
