# ============================================================
#  sprites.py
#  Contains:
#    - All constants (screen size, speed, colours, coin tiers)
#    - All Sprite classes (Player, Enemy, Coin)
#  Imported by main.py which runs the game loop.
# ============================================================

import pygame
from pygame.locals import K_LEFT, K_RIGHT
import random
import os

# ---- Path helper ----
# Use the folder of THIS file as the base so images load correctly
# no matter where the user launches the game from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
#  Colours
# ============================================================
BLUE         = (0,   0,   255)
RED          = (255, 0,   0)
GREEN        = (0,   255, 0)
BLACK        = (0,   0,   0)
WHITE        = (255, 255, 255)
YELLOW       = (255, 215, 0)    # Used for HUD coin counter

BRONZE_COLOR = (205, 127,  50)  # 1-point coin — common
SILVER_COLOR = (192, 192, 192)  # 3-point coin — uncommon
GOLD_COLOR   = (255, 215,   0)  # 5-point coin — rare

# ============================================================
#  Screen & Timing Constants
# ============================================================
SCREEN_WIDTH  = 400
SCREEN_HEIGHT = 600
FPS           = 60   # Target frames per second

# ============================================================
#  Difficulty Constants
# ============================================================
INITIAL_SPEED        = 5     # Starting fall speed for enemies
COIN_SPEED_MILESTONE = 10    # Every N coin-points → speed boost fires
COIN_SPEED_BOOST     = 0.8   # How much SPEED increases per milestone
TIME_SPEED_BOOST     = 0.5   # How much SPEED increases every second (timer event)

# ============================================================
#  Coin Tier Definitions  (Feature 1 — weighted coins)
# ============================================================
#  Each tier is a dict with:
#    color  — RGB tuple drawn on the coin circle
#    value  — points awarded when collected
#    weight — relative spawn probability (higher = more common)
#
#  random.choices() uses these weights so Bronze (~60 %) appears
#  far more often than Gold (~10 %).
# ============================================================
COIN_TIERS = [
    {"color": BRONZE_COLOR, "value": 1, "weight": 60},  # common
    {"color": SILVER_COLOR, "value": 3, "weight": 30},  # uncommon
    {"color": GOLD_COLOR,   "value": 5, "weight": 10},  # rare
]

# Pre-extracted weight list consumed by random.choices()
_TIER_WEIGHTS = [t["weight"] for t in COIN_TIERS]


# ============================================================
#  Sprite: Enemy
# ============================================================
class Enemy(pygame.sprite.Sprite):
    """Oncoming obstacle car.

    Falls from the top of the screen at the current global speed.
    When it exits the bottom unharmed, the score increases by 1
    and it respawns at the top.

    Args:
        speed_ref (list): A one-element list [float] shared with main.py
                          so the sprite always reads the live speed value.
        score_ref (list): A one-element list [int] shared with main.py
                          so the sprite can increment the score directly.
    """

    def __init__(self, speed_ref: list, score_ref: list, *groups):
        super().__init__(*groups)
        # speed_ref and score_ref are mutable containers so changes made
        # here are visible in main.py without using 'global'.
        self._speed = speed_ref
        self._score = score_ref
        self.image  = pygame.image.load(os.path.join(BASE_DIR, "images", "Enemy.png"))
        self.rect   = self.image.get_rect()
        self._place_at_top()

    def _place_at_top(self):
        """Spawn or respawn at a random x position along the top edge."""
        self.rect.center = (random.randint(40, SCREEN_WIDTH - 40), 0)

    def move(self):
        """Move the enemy down and recycle when it leaves the screen."""
        self.rect.move_ip(0, self._speed[0])
        if self.rect.bottom > SCREEN_HEIGHT:
            self._score[0] += 1       # increment shared score counter
            self._place_at_top()


# ============================================================
#  Sprite: Player
# ============================================================
class Player(pygame.sprite.Sprite):
    """The player's car — controlled with LEFT / RIGHT arrow keys.

    Movement is clamped to the screen edges so the car can never
    leave the visible road area.
    """

    def __init__(self, *groups):
        super().__init__(*groups)
        self.image = pygame.image.load(os.path.join(BASE_DIR, "images", "Player.png"))
        self.rect  = self.image.get_rect()
        self.rect.center = (160, 520)   # Start near bottom-centre of screen

    def move(self):
        """Read keyboard state and move left / right."""
        pressed_keys = pygame.key.get_pressed()
        if self.rect.left > 0 and pressed_keys[K_LEFT]:
            self.rect.move_ip(-5, 0)
        if self.rect.right < SCREEN_WIDTH and pressed_keys[K_RIGHT]:
            self.rect.move_ip(5, 0)


# ============================================================
#  Sprite: Coin  (Feature 1 — weighted tiers)
# ============================================================
class Coin(pygame.sprite.Sprite):
    """A collectible coin that falls from the top of the screen.

    Each time a Coin spawns or respawns, a tier is chosen at random
    using the weights defined in COIN_TIERS.  The coin is drawn as a
    filled circle in the tier's colour with a thin black border.

    Attributes:
        value (int): Point value of the current tier (1, 3, or 5).

    Args:
        speed_ref (list): One-element list [float] with the live speed.
    """

    def __init__(self, speed_ref: list, *groups):
        super().__init__(*groups)
        self._speed = speed_ref
        # Create a transparent 20×20 surface for the coin graphic
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        self.rect  = self.image.get_rect()
        self._assign_tier()   # draw initial appearance + set self.value
        self.rect.center = (random.randint(20, SCREEN_WIDTH - 20), 0)

    # ---- Internal helpers ----

    def _assign_tier(self):
        """Pick a random tier (weighted) and redraw the coin surface."""
        tier       = random.choices(COIN_TIERS, weights=_TIER_WEIGHTS, k=1)[0]
        self.value = tier["value"]             # 1, 3, or 5 points
        self.image.fill((0, 0, 0, 0))          # clear to transparent first
        pygame.draw.circle(self.image, tier["color"], (10, 10), 10)
        pygame.draw.circle(self.image, BLACK,          (10, 10), 10, 2)  # border

    def _respawn(self):
        """Recycle coin: pick a new tier and move back to the top."""
        self._assign_tier()
        self.rect.center = (random.randint(20, SCREEN_WIDTH - 20), 0)

    # ---- Public method ----

    def move(self):
        """Fall at 60 % of enemy speed; respawn if it exits the bottom."""
        self.rect.move_ip(0, self._speed[0] * 0.6)
        if self.rect.top > SCREEN_HEIGHT:
            self._respawn()
