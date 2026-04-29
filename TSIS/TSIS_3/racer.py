# ============================================================
#  racer.py  —  TSIS 3
#  All sprite/entity classes:
#    Player, Enemy, Coin, Obstacle, PowerUp
#  Plus all game constants.
# ============================================================

import pygame
from pygame.locals import K_LEFT, K_RIGHT, K_UP, K_DOWN
import random
import os

_HERE    = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = _HERE   # kept for compatibility with asset loader

# ============================================================
#  Colours
# ============================================================
BLACK        = (0,   0,   0)
WHITE        = (255, 255, 255)
RED          = (255, 0,   0)
GREEN        = (0,   200, 0)
BLUE         = (0,   0,   255)
YELLOW       = (255, 215, 0)
ORANGE       = (255, 140, 0)
SILVER_COLOR = (192, 192, 192)
DARK_GRAY    = (50,  50,  50)
ROAD_GRAY    = (80,  80,  80)
LANE_WHITE   = (240, 240, 240)
NITRO_COLOR  = (0,   220, 255)
SHIELD_COLOR = (100, 100, 255)
REPAIR_COLOR = (0,   220, 80)
OIL_COLOR    = (80,  20, 120)   # dark purple — visible on road
BUMP_COLOR   = (200, 100,  20)

# ============================================================
#  Screen & Timing
# ============================================================
SCREEN_WIDTH  = 400
SCREEN_HEIGHT = 600
FPS           = 60

# Lane definitions (3 lanes)
LANE_CENTERS = [80, 200, 320]
LANE_COUNT   = 3

# ============================================================
#  Difficulty Presets
# ============================================================
DIFFICULTY = {
    "easy":   {"initial_speed": 4,  "time_boost": 0.3, "enemy_count": 1, "obstacle_rate": 90},
    "normal": {"initial_speed": 5,  "time_boost": 0.5, "enemy_count": 2, "obstacle_rate": 60},
    "hard":   {"initial_speed": 7,  "time_boost": 0.8, "enemy_count": 3, "obstacle_rate": 40},
}

INITIAL_SPEED        = 5
COIN_SPEED_MILESTONE = 10
COIN_SPEED_BOOST     = 0.8
TIME_SPEED_BOOST     = 0.5

# ============================================================
#  Coin Tiers  (from Practice 11 — kept as-is)
# ============================================================
BRONZE_COLOR = (205, 127,  50)
SILVER_COL   = (192, 192, 192)
GOLD_COLOR   = (255, 215,   0)

COIN_TIERS = [
    {"color": BRONZE_COLOR, "value": 1, "weight": 60},
    {"color": SILVER_COL,   "value": 3, "weight": 30},
    {"color": GOLD_COLOR,   "value": 5, "weight": 10},
]
_TIER_WEIGHTS = [t["weight"] for t in COIN_TIERS]

# ============================================================
#  Power-up types
# ============================================================
POWERUP_TYPES = ["nitro", "shield", "repair"]
POWERUP_COLORS = {
    "nitro":  NITRO_COLOR,
    "shield": SHIELD_COLOR,
    "repair": REPAIR_COLOR,
}
POWERUP_DURATION = {
    "nitro":  4 * FPS,   # 4 seconds in frames
    "shield": 0,         # until hit (handled in main)
    "repair": 0,         # instant
}


# ============================================================
#  Helper: safe image load (fallback to coloured rect)
# ============================================================
def _load_image(name, fallback_size, fallback_color):
    path = os.path.join(_HERE, "images", name)
    if os.path.exists(path):
        try:
            return pygame.image.load(path).convert_alpha()
        except pygame.error:
            pass
    surf = pygame.Surface(fallback_size, pygame.SRCALPHA)
    surf.fill(fallback_color)
    return surf


# ============================================================
#  Sprite: Player
# ============================================================
class Player(pygame.sprite.Sprite):
    """Player car — moves left/right with arrow keys, optionally up/down."""

    CAR_COLORS = {
        "blue":   BLUE,
        "red":    RED,
        "yellow": YELLOW,
    }

    def __init__(self, speed_ref: list, car_color: str = "blue"):
        super().__init__()
        self._speed = speed_ref
        color       = self.CAR_COLORS.get(car_color, BLUE)

        img = _load_image("Player.png", (40, 70), color)
        # Tint the image if a colour was chosen and the file exists
        self.image = img
        self.rect  = self.image.get_rect()
        self.rect.center = (LANE_CENTERS[1], 520)

        self.has_shield  = False
        self.nitro_timer = 0      # frames remaining for nitro

    def move(self):
        pressed = pygame.key.get_pressed()
        # Nitro boosts speed; oil slows it; default is 5
        if self.nitro_timer > 0:
            spd = 7
            self.nitro_timer -= 1
        elif getattr(self, "slowed", False):
            spd = 2
        else:
            spd = 5

        if self.rect.left > 0             and pressed[K_LEFT]:  self.rect.move_ip(-spd, 0)
        if self.rect.right < SCREEN_WIDTH  and pressed[K_RIGHT]: self.rect.move_ip( spd, 0)
        if self.rect.top > 80             and pressed[K_UP]:    self.rect.move_ip(0, -spd)
        if self.rect.bottom < SCREEN_HEIGHT and pressed[K_DOWN]: self.rect.move_ip(0,  spd)


# ============================================================
#  Sprite: Enemy  (traffic car)
# ============================================================
class Enemy(pygame.sprite.Sprite):
    def __init__(self, speed_ref: list, score_ref: list):
        super().__init__()
        self._speed = speed_ref
        self._score = score_ref
        self.image  = _load_image("Enemy.png", (40, 70), RED)
        self.rect   = self.image.get_rect()
        self._place_at_top()

    def _place_at_top(self):
        lane = random.choice(LANE_CENTERS)
        self.rect.center = (lane, -80)

    def move(self):
        self.rect.move_ip(0, self._speed[0])
        if self.rect.top > SCREEN_HEIGHT:
            self._score[0] += 1
            self._place_at_top()


# ============================================================
#  Sprite: Coin  (weighted tiers — from Practice 11)
# ============================================================
class Coin(pygame.sprite.Sprite):
    def __init__(self, speed_ref: list):
        super().__init__()
        self._speed = speed_ref
        self.image  = pygame.Surface((20, 20), pygame.SRCALPHA)
        self.rect   = self.image.get_rect()
        self._assign_tier()
        self.rect.center = (random.randint(20, SCREEN_WIDTH - 20), -20)

    def _assign_tier(self):
        tier       = random.choices(COIN_TIERS, weights=_TIER_WEIGHTS, k=1)[0]
        self.value = tier["value"]
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, tier["color"], (10, 10), 10)
        pygame.draw.circle(self.image, BLACK,          (10, 10), 10, 2)

    def _respawn(self):
        self._assign_tier()
        self.rect.center = (random.randint(20, SCREEN_WIDTH - 20), -20)

    def move(self):
        self.rect.move_ip(0, self._speed[0] * 0.6)
        if self.rect.top > SCREEN_HEIGHT:
            self._respawn()


# ============================================================
#  Sprite: Obstacle (oil spill / speed bump / barrier)
# ============================================================
OBSTACLE_TYPES = ["oil", "bump", "barrier"]

class Obstacle(pygame.sprite.Sprite):
    """Road hazard that slows or kills the player."""

    def __init__(self, speed_ref: list, obs_type: str = None):
        super().__init__()
        self._speed   = speed_ref
        self.obs_type = obs_type or random.choice(OBSTACLE_TYPES)
        self.image    = self._make_surface()
        self.rect     = self.image.get_rect()
        self._place_at_top()

    def _make_surface(self):
        if self.obs_type == "oil":
            surf = pygame.Surface((50, 30), pygame.SRCALPHA)
            pygame.draw.ellipse(surf, (*OIL_COLOR, 220), (0, 0, 50, 30))
            # Purple shimmer border so it's clearly visible on dark road
            pygame.draw.ellipse(surf, (180, 80, 255, 180), (0, 0, 50, 30), 3)
            return surf
        elif self.obs_type == "bump":
            surf = pygame.Surface((60, 18), pygame.SRCALPHA)
            pygame.draw.rect(surf, BUMP_COLOR, (0, 0, 60, 18), border_radius=6)
            return surf
        else:  # barrier
            surf = pygame.Surface((20, 50), pygame.SRCALPHA)
            pygame.draw.rect(surf, ORANGE, (0, 0, 20, 50), border_radius=4)
            pygame.draw.rect(surf, WHITE,  (0, 0, 20, 50), 2, border_radius=4)
            return surf

    def _place_at_top(self):
        lane = random.choice(LANE_CENTERS)
        self.rect.centerx = lane + random.randint(-20, 20)
        self.rect.bottom  = -10

    def move(self):
        spd = self._speed[0] * (0.7 if self.obs_type == "bump" else 0.9)
        self.rect.move_ip(0, spd)
        if self.rect.top > SCREEN_HEIGHT:
            self._place_at_top()


# ============================================================
#  Sprite: PowerUp
# ============================================================
class PowerUp(pygame.sprite.Sprite):
    TIMEOUT = 8 * FPS   # disappears after 8 seconds if not collected

    def __init__(self, speed_ref: list, kind: str = None):
        super().__init__()
        self._speed   = speed_ref
        self.kind     = kind or random.choice(POWERUP_TYPES)
        self.image    = self._make_surface()
        self.rect     = self.image.get_rect()
        self._timer   = self.TIMEOUT
        self.rect.center = (
            random.choice(LANE_CENTERS),
            random.randint(-200, -40),
        )

    def _make_surface(self):
        color = POWERUP_COLORS[self.kind]
        surf  = pygame.Surface((28, 28), pygame.SRCALPHA)
        pygame.draw.circle(surf, color, (14, 14), 14)
        pygame.draw.circle(surf, WHITE, (14, 14), 14, 2)
        # Letter label
        font = pygame.font.SysFont("Verdana", 13, bold=True)
        lbl  = {"nitro": "N", "shield": "S", "repair": "R"}[self.kind]
        txt  = font.render(lbl, True, BLACK)
        surf.blit(txt, txt.get_rect(center=(14, 14)))
        return surf

    def move(self):
        self.rect.move_ip(0, self._speed[0] * 0.5)
        self._timer -= 1
        if self.rect.top > SCREEN_HEIGHT or self._timer <= 0:
            self.kill()


# ============================================================
#  Sprite: NitroStrip (road feature — speed-boost strip)
# ============================================================
class NitroStrip(pygame.sprite.Sprite):
    """Decorative road strip; treated as a power-up zone."""

    def __init__(self, speed_ref: list):
        super().__init__()
        self._speed = speed_ref
        self.image  = pygame.Surface((SCREEN_WIDTH, 18), pygame.SRCALPHA)
        for i in range(0, SCREEN_WIDTH, 20):
            pygame.draw.rect(self.image, (*NITRO_COLOR, 120), (i, 0, 10, 18))
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom   = -10

    def move(self):
        self.rect.move_ip(0, self._speed[0])
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()
