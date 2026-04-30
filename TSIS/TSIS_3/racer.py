# ============================================================
#  racer.py  —  TSIS 3
#  All sprite/entity classes:
#    Player, Enemy, Coin, Obstacle, PowerUp
#  Plus all game constants.
# ============================================================
# This file is the "game engine core" — it defines every moving object
# in the game and all the numeric constants that control gameplay feel.
# main.py imports everything from here; racer.py itself has no game loop.

import pygame
# pygame — the game library. Needed here for Surface, Rect, sprite classes,
# drawing functions, font rendering, and keyboard input.

from pygame.locals import K_LEFT, K_RIGHT, K_UP, K_DOWN
# Import the four arrow-key constants directly so we can write
# pressed[K_LEFT] instead of pressed[pygame.K_LEFT] — shorter and cleaner.

import random
# random — used for random lane selection, tier picking, spawn positions, etc.

import os
# os — used to build cross-platform file paths to images and assets.

_HERE    = os.path.dirname(os.path.abspath(__file__))
# _HERE = absolute path to the folder containing racer.py.
# Used to locate the "images/" subfolder regardless of where the game is launched from.

BASE_DIR = _HERE   # kept for compatibility with asset loader
# An alias for _HERE. Some older code or other modules may reference BASE_DIR,
# so we keep this name to avoid breaking anything.

# ============================================================
#  Colours
# ============================================================
# All colours are RGB tuples: (Red, Green, Blue), each value 0–255.
# Defined once here so every sprite can import and reuse them
# instead of scattering magic numbers throughout the code.

BLACK        = (0,   0,   0)    # Pure black — used for outlines, text
WHITE        = (255, 255, 255)  # Pure white — used for lane lines, outlines
RED          = (255, 0,   0)    # Bright red — enemy cars
GREEN        = (0,   200, 0)    # Mid green — UI accents
BLUE         = (0,   0,   255)  # Bright blue — default player car color
YELLOW       = (255, 215, 0)    # Gold-yellow — coins, player color option
ORANGE       = (255, 140, 0)    # Orange — barrier obstacles
SILVER_COLOR = (192, 192, 192)  # Silver — silver coin tier
DARK_GRAY    = (50,  50,  50)   # Very dark gray — unused directly but available
ROAD_GRAY    = (80,  80,  80)   # Road surface color (used in ui.py's draw_road)
LANE_WHITE   = (240, 240, 240)  # Near-white — lane divider lines
NITRO_COLOR  = (0,   220, 255)  # Cyan — nitro power-up and nitro strip
SHIELD_COLOR = (100, 100, 255)  # Soft blue — shield power-up
REPAIR_COLOR = (0,   220, 80)   # Bright green — repair power-up
OIL_COLOR    = (80,  20, 120)   # Dark purple — oil spill obstacle
BUMP_COLOR   = (200, 100,  20)  # Brown-orange — speed bump obstacle

# ============================================================
#  Screen & Timing
# ============================================================
SCREEN_WIDTH  = 400   # Window width in pixels
SCREEN_HEIGHT = 600   # Window height in pixels
FPS           = 60    # Target frames per second — controls game loop speed

# Lane definitions (3 lanes)
LANE_CENTERS = [80, 200, 320]
# X-coordinates (pixels from left) of the center of each of the 3 driving lanes.
# Lane 0 (left): x=80, Lane 1 (middle): x=200, Lane 2 (right): x=320.
# Sprites snap to these centers when spawning to stay inside lane boundaries.

LANE_COUNT   = 3
# Total number of lanes — used for reference in case lane logic needs to be generalized.

# ============================================================
#  Difficulty Presets
# ============================================================
DIFFICULTY = {
    # Each key is a difficulty name; each value is a dict of gameplay parameters.
    "easy":   {"initial_speed": 4,  "time_boost": 0.3, "enemy_count": 1, "obstacle_rate": 90},
    # easy:   Slow start (4), gentle speed increase (0.3/sec), 1 enemy, obstacle every 90 frames (~1.5s)
    "normal": {"initial_speed": 5,  "time_boost": 0.5, "enemy_count": 2, "obstacle_rate": 60},
    # normal: Medium start (5), moderate increase (0.5/sec), 2 enemies, obstacle every 60 frames (1s)
    "hard":   {"initial_speed": 7,  "time_boost": 0.8, "enemy_count": 3, "obstacle_rate": 40},
    # hard:   Fast start (7), aggressive increase (0.8/sec), 3 enemies, obstacle every 40 frames (~0.67s)
}

INITIAL_SPEED        = 5
# Default starting speed (pixels per frame) used as a fallback constant.
# The actual starting speed comes from DIFFICULTY[diff_key]["initial_speed"] in main.py.

COIN_SPEED_MILESTONE = 10
# How many coins must be collected to trigger a speed boost.
# Every 10 coins collected = one COIN_SPEED_BOOST added to road speed.

COIN_SPEED_BOOST     = 0.8
# Speed increase (pixels/frame) rewarded for hitting a coin milestone.

TIME_SPEED_BOOST     = 0.5
# Speed increase (pixels/frame) applied automatically every second of survival.
# This is what makes the game progressively harder the longer you play.

# ============================================================
#  Coin Tiers  (from Practice 11 — kept as-is)
# ============================================================
# Coins come in three visual tiers with different point values and spawn probabilities.

BRONZE_COLOR = (205, 127,  50)  # Brownish — common, low-value coins
SILVER_COL   = (192, 192, 192)  # Silver   — uncommon, medium-value coins
GOLD_COLOR   = (255, 215,   0)  # Gold     — rare, high-value coins

COIN_TIERS = [
    {"color": BRONZE_COLOR, "value": 1, "weight": 60},
    # Bronze: worth 1 point, appears 60% of the time (most common)
    {"color": SILVER_COL,   "value": 3, "weight": 30},
    # Silver: worth 3 points, appears 30% of the time
    {"color": GOLD_COLOR,   "value": 5, "weight": 10},
    # Gold:   worth 5 points, appears 10% of the time (rarest)
]
# Each dict has:
#   "color"  — RGB tuple drawn as the coin's fill color
#   "value"  — points added to coins_total when collected
#   "weight" — relative probability used by random.choices()

_TIER_WEIGHTS = [t["weight"] for t in COIN_TIERS]
# Extract just the weights into a plain list: [60, 30, 10]
# Pre-computed here once so random.choices() in Coin._assign_tier()
# doesn't rebuild it from scratch on every coin spawn.

# ============================================================
#  Power-up types
# ============================================================
POWERUP_TYPES = ["nitro", "shield", "repair"]
# List of all possible power-up kinds. Used by PowerUp.__init__() to pick one at random.

POWERUP_COLORS = {
    "nitro":  NITRO_COLOR,   # Cyan circle — speed boost
    "shield": SHIELD_COLOR,  # Blue circle — absorbs one hit
    "repair": REPAIR_COLOR,  # Green circle — clears all obstacles instantly
}
# Maps each power-up kind to its display color, used when drawing the power-up sprite.

POWERUP_DURATION = {
    "nitro":  4 * FPS,   # 4 seconds × 60 FPS = 240 frames before nitro expires
    "shield": 0,         # Shield has no timer — lasts until the player takes a hit
    "repair": 0,         # Repair is instant — no duration to track
}
# Duration in frames for each power-up type.
# main.py sets G["pu_timer"] to this value when a power-up is collected.


# ============================================================
#  Helper: safe image load (fallback to coloured rect)
# ============================================================
def _load_image(name, fallback_size, fallback_color):
    # Attempts to load a PNG image from the "images/" folder.
    # If the file doesn't exist or fails to load, creates a plain colored rectangle instead.
    # This way sprites always have a visible image even without an art folder.
    # Arguments:
    #   name           — filename, e.g. "Player.png"
    #   fallback_size  — (width, height) tuple used if the file is missing
    #   fallback_color — RGB color tuple for the fallback rectangle

    path = os.path.join(_HERE, "images", name)
    # Build the full path, e.g. "C:/projects/cardodge/images/Player.png"

    if os.path.exists(path):
        # The file exists — try to load it.
        try:
            return pygame.image.load(path).convert_alpha()
            # pygame.image.load() reads the PNG into a Surface.
            # .convert_alpha() converts the pixel format to match the display
            # AND preserves the transparency channel — essential for PNG sprites
            # that have transparent backgrounds.
        except pygame.error:
            pass
            # If pygame can't decode the image (wrong format, corrupt file, etc.),
            # silently fall through to create the fallback surface below.

    surf = pygame.Surface(fallback_size, pygame.SRCALPHA)
    # Create a blank surface with the given size.
    # pygame.SRCALPHA means the surface supports per-pixel transparency (alpha channel).

    surf.fill(fallback_color)
    # Fill the entire surface with the fallback color.
    # Result: a solid colored rectangle that acts as a placeholder sprite.

    return surf
    # Return either the loaded PNG or the colored rectangle.


# ============================================================
#  Sprite: Player
# ============================================================
class Player(pygame.sprite.Sprite):
    """Player car — moves left/right with arrow keys, optionally up/down."""
    # Inherits from pygame.sprite.Sprite, giving us:
    #   self.image — the Surface drawn to the screen
    #   self.rect  — the Rect controlling position and used for collision detection
    #   self.kill()— removes the sprite from all its groups

    CAR_COLORS = {
        "blue":   BLUE,    # (0, 0, 255)
        "red":    RED,     # (255, 0, 0)
        "yellow": YELLOW,  # (255, 215, 0)
    }
    # Maps user-facing color name strings to RGB tuples.
    # Used to tint the fallback rectangle when Player.png is missing.

    def __init__(self, speed_ref: list, car_color: str = "blue"):
        # Constructor — sets up the player sprite.
        # speed_ref: the shared [speed] list from main.py (passed by reference).
        # car_color: the player's chosen color string ("blue", "red", or "yellow").

        super().__init__()
        # Call pygame.sprite.Sprite.__init__() — required to properly register
        # this object as a sprite and initialize internal pygame sprite state.

        self._speed = speed_ref
        # Store the reference to the shared speed list.
        # self._speed[0] always reflects the current road speed set by main.py.

        color = self.CAR_COLORS.get(car_color, BLUE)
        # Look up the RGB tuple for the chosen color.
        # .get(car_color, BLUE) returns BLUE as a default if car_color is unrecognized.

        img = _load_image("Player.png", (40, 70), color)
        # Try to load Player.png (40×70 pixels). If missing, create a 40×70 colored rect.

        # Tint the image if a colour was chosen and the file exists
        self.image = img
        # Assign the loaded/fallback surface as the sprite's visible image.

        self.rect  = self.image.get_rect()
        # Create a Rect the same size as the image.
        # self.rect controls where the sprite is positioned on screen and
        # is what pygame uses for collision detection (.colliderect(), spritecollide(), etc.).

        self.rect.center = (LANE_CENTERS[1], 520)
        # Place the player at the center lane (index 1 = x=200) near the bottom of the screen (y=520).
        # This is the starting position at the beginning of every game.

        self.has_shield  = False
        # Flag: True when the shield power-up is active.
        # Checked in main.py on every collision — if True, the hit is absorbed instead of crashing.

        self.nitro_timer = 0
        # Frames remaining for the player's own nitro effect (internal to Player.move()).
        # Note: the main nitro power-up is tracked separately in G["pu_timer"] in main.py.
        # This timer is currently initialized but not set from outside — it's a leftover
        # from an earlier design where the player managed their own nitro countdown.

    def move(self):
        # Called every frame to update the player's position based on keyboard input.
        # Handles movement speed modifiers (nitro boost, oil slow).

        pressed = pygame.key.get_pressed()
        # Returns a sequence of booleans indexed by key constant.
        # pressed[K_LEFT] is True if the left arrow key is currently held down.

        # Nitro boosts speed; oil slows it; default is 5
        if self.nitro_timer > 0:
            spd = 7
            # Player is under internal nitro effect — move faster (7 px/frame).
            self.nitro_timer -= 1
            # Tick the internal nitro timer down each frame.
        elif getattr(self, "slowed", False):
            spd = 2
            # Player hit an oil spill — movement capped at 2 px/frame.
            # getattr(self, "slowed", False) safely checks for the attribute
            # without crashing if it was never set (defaults to False).
        else:
            spd = 5
            # Normal movement speed: 5 pixels per frame (constant, not tied to road speed).

        if self.rect.left > 0             and pressed[K_LEFT]:  self.rect.move_ip(-spd, 0)
        # Move LEFT by `spd` pixels, but only if the left edge of the car
        # hasn't reached the left edge of the screen (rect.left > 0 = not at wall).

        if self.rect.right < SCREEN_WIDTH  and pressed[K_RIGHT]: self.rect.move_ip( spd, 0)
        # Move RIGHT, but only if the right edge hasn't hit the right screen boundary.

        if self.rect.top > 80             and pressed[K_UP]:    self.rect.move_ip(0, -spd)
        # Move UP, but only if the top of the car is below y=80 (keeps the car
        # below the HUD area so it doesn't go behind the score display).

        if self.rect.bottom < SCREEN_HEIGHT and pressed[K_DOWN]: self.rect.move_ip(0,  spd)
        # Move DOWN, but only if the bottom of the car hasn't hit the bottom of the screen.

        # move_ip() = "move in place" — modifies self.rect directly (no return value).
        # The two arguments are (delta_x, delta_y): positive x = right, positive y = down.


# ============================================================
#  Sprite: Enemy  (traffic car)
# ============================================================
class Enemy(pygame.sprite.Sprite):
    # An oncoming traffic car that scrolls from the top of the screen to the bottom.
    # When it exits the screen, it respawns at the top and awards 1 point.
    # Colliding with the player ends the game (unless the player has a shield).

    def __init__(self, speed_ref: list, score_ref: list):
        # speed_ref: shared [speed] list — enemy moves at the same rate as the road.
        # score_ref: shared [score] list — incremented each time an enemy is dodged.

        super().__init__()
        # Initialize pygame.sprite.Sprite base class.

        self._speed = speed_ref
        # Store the speed reference. self._speed[0] gives the current speed.

        self._score = score_ref
        # Store the score reference. self._score[0] is incremented when dodged.

        self.image  = _load_image("Enemy.png", (40, 70), RED)
        # Load the enemy car image (40×70 px). Falls back to a red rectangle.

        self.rect   = self.image.get_rect()
        # Create the bounding Rect for position and collision.

        self._place_at_top()
        # Set the initial spawn position at the top of the screen.

    def _place_at_top(self):
        # Teleport the enemy to a random lane above the visible screen.
        # Called at init and whenever the enemy exits the bottom.

        lane = random.choice(LANE_CENTERS)
        # Pick one of [80, 200, 320] at random.

        self.rect.center = (lane, -80)
        # Place the enemy 80 pixels ABOVE the top of the screen (y=-80).
        # It scrolls down into view naturally as move() runs each frame.

    def move(self):
        # Called every frame. Scrolls the enemy downward at road speed.

        self.rect.move_ip(0, self._speed[0])
        # Move downward by speed[0] pixels — same speed as the road scroll
        # so enemies appear to stay at fixed positions relative to the road.

        if self.rect.top > SCREEN_HEIGHT:
            # The enemy has fully scrolled off the bottom of the screen.
            self._score[0] += 1
            # Award 1 point for successfully dodging this enemy.
            self._place_at_top()
            # Respawn at the top to create an endless stream of traffic.


# ============================================================
#  Sprite: Coin  (weighted tiers — from Practice 11)
# ============================================================
class Coin(pygame.sprite.Sprite):
    # A collectible coin that scrolls down the screen.
    # Coins have three tiers (bronze/silver/gold) with different values and rarities.
    # When collected or off-screen, they respawn at the top rather than being destroyed.

    def __init__(self, speed_ref: list):
        super().__init__()
        # Initialize pygame.sprite.Sprite base class.

        self._speed = speed_ref
        # Store speed reference so the coin scrolls at a fraction of road speed.

        self.image  = pygame.Surface((20, 20), pygame.SRCALPHA)
        # Create a 20×20 transparent surface to draw the coin circle onto.
        # pygame.SRCALPHA enables per-pixel alpha so the circle has no square corners.

        self.rect   = self.image.get_rect()
        # Create the bounding Rect.

        self._assign_tier()
        # Randomly pick a coin tier (bronze/silver/gold) and draw the coin on self.image.

        self.rect.center = (random.randint(20, SCREEN_WIDTH - 20), -20)
        # Place the coin at a random horizontal position (20px margin from edges)
        # and 20px above the top of the screen so it scrolls into view smoothly.

    def _assign_tier(self):
        # Randomly selects a coin tier and redraws self.image with that tier's color and value.
        # Called both at creation and on respawn so each appearance can be a different tier.

        tier       = random.choices(COIN_TIERS, weights=_TIER_WEIGHTS, k=1)[0]
        # random.choices() picks 1 item from COIN_TIERS using the weighted probabilities.
        # weights=_TIER_WEIGHTS = [60, 30, 10] → 60% bronze, 30% silver, 10% gold.
        # k=1 means pick 1 item; [0] unpacks the single-element list to get the dict.

        self.value = tier["value"]
        # Store this coin's point value (1, 3, or 5) for when it's collected in main.py.

        self.image.fill((0, 0, 0, 0))
        # Clear the surface to fully transparent (RGBA 0,0,0,0) before redrawing.
        # Necessary on respawn so the old coin color doesn't show through.

        pygame.draw.circle(self.image, tier["color"], (10, 10), 10)
        # Draw a filled circle: center=(10,10) within the 20×20 surface, radius=10.
        # This fills the entire surface edge-to-edge with the tier's color.

        pygame.draw.circle(self.image, BLACK, (10, 10), 10, 2)
        # Draw a 2-pixel-wide black outline around the circle for definition.
        # The 5th argument (width=2) makes it an outline instead of a filled circle.

    def _respawn(self):
        # Reset the coin to a new random position and tier.
        # Called from main.py when the player collects this coin.
        # Using respawn instead of kill+create avoids the overhead of creating new objects.

        self._assign_tier()
        # Pick a new random tier and redraw the coin image.

        self.rect.center = (random.randint(20, SCREEN_WIDTH - 20), -20)
        # Move the coin back to a random x position above the screen top.

    def move(self):
        # Called every frame. Scrolls the coin downward at 60% of road speed.

        self.rect.move_ip(0, self._speed[0] * 0.6)
        # Coins move slower than the road (×0.6) so they feel like they're
        # floating slightly ahead — easier to see and react to.

        if self.rect.top > SCREEN_HEIGHT:
            # Coin scrolled off the bottom without being collected.
            self._respawn()
            # Bring it back above the screen so there's always a coin available.


# ============================================================
#  Sprite: Obstacle (oil spill / speed bump / barrier)
# ============================================================
OBSTACLE_TYPES = ["oil", "bump", "barrier"]
# The three obstacle varieties. Randomly selected when spawning unless overridden.
# "oil"     — slows the player for 3 seconds
# "bump"    — crashes the player (unless shielded)
# "barrier" — crashes the player (unless shielded)

class Obstacle(pygame.sprite.Sprite):
    """Road hazard that slows or kills the player."""

    def __init__(self, speed_ref: list, obs_type: str = None):
        # speed_ref: shared speed list.
        # obs_type:  if provided, forces this specific type; otherwise random.

        super().__init__()

        self._speed   = speed_ref
        # Store speed reference for scrolling.

        self.obs_type = obs_type or random.choice(OBSTACLE_TYPES)
        # Use the specified type, or pick one randomly from ["oil", "bump", "barrier"].
        # `or` short-circuits: if obs_type is None/empty, random.choice() is called.

        self.image    = self._make_surface()
        # Draw the obstacle's visual appearance based on its type.

        self.rect     = self.image.get_rect()
        # Create the bounding Rect.

        self._place_at_top()
        # Set starting position above the screen.

    def _make_surface(self):
        # Creates and returns the appropriate Surface for this obstacle type.
        # Each type has a distinct shape and color so the player can react differently.

        if self.obs_type == "oil":
            surf = pygame.Surface((50, 30), pygame.SRCALPHA)
            # 50×30 transparent surface for the ellipse-shaped spill.

            pygame.draw.ellipse(surf, (*OIL_COLOR, 220), (0, 0, 50, 30))
            # Draw a filled ellipse covering the full surface.
            # (*OIL_COLOR, 220) unpacks (80, 20, 120) and adds alpha=220 (nearly opaque).
            # The ellipse shape suggests a liquid puddle on the road.

            pygame.draw.ellipse(surf, (180, 80, 255, 180), (0, 0, 50, 30), 3)
            # Draw a 3px-wide purple shimmer border on top.
            # Makes the oil spill clearly visible against the dark road surface.

            return surf

        elif self.obs_type == "bump":
            surf = pygame.Surface((60, 18), pygame.SRCALPHA)
            # 60×18 transparent surface — wide and flat, like a speed bump.

            pygame.draw.rect(surf, BUMP_COLOR, (0, 0, 60, 18), border_radius=6)
            # Draw a rounded rectangle in brown-orange.
            # border_radius=6 softens the corners to look more like a physical bump.

            return surf

        else:  # barrier
            surf = pygame.Surface((20, 50), pygame.SRCALPHA)
            # 20×50 transparent surface — tall and narrow, like a traffic cone or post.

            pygame.draw.rect(surf, ORANGE, (0, 0, 20, 50), border_radius=4)
            # Fill with orange.

            pygame.draw.rect(surf, WHITE,  (0, 0, 20, 50), 2, border_radius=4)
            # Draw a 2px white border outline — makes the barrier pop visually.

            return surf

    def _place_at_top(self):
        # Position the obstacle just above the top of the screen in a random lane.

        lane = random.choice(LANE_CENTERS)
        # Pick a random lane center x-coordinate.

        self.rect.centerx = lane + random.randint(-20, 20)
        # Add a small random horizontal offset (±20px) so obstacles aren't always
        # perfectly centered in the lane — adds visual variety.

        self.rect.bottom  = -10
        # Place the bottom of the obstacle 10px above the screen top (y=-10).
        # The obstacle scrolls downward into view from here.

    def move(self):
        # Called every frame. Scrolls the obstacle downward and respawns it when off-screen.

        spd = self._speed[0] * (0.7 if self.obs_type == "bump" else 0.9)
        # Bumps move at 70% of road speed (they're heavy/slow on the road).
        # Oil spills and barriers move at 90% (closer to road speed).
        # This subtle difference makes each obstacle feel physically distinct.

        self.rect.move_ip(0, spd)
        # Move downward by the calculated speed.

        if self.rect.top > SCREEN_HEIGHT:
            # Obstacle has scrolled off the bottom of the screen.
            self._place_at_top()
            # Respawn above the screen for the next pass.


# ============================================================
#  Sprite: PowerUp
# ============================================================
class PowerUp(pygame.sprite.Sprite):
    # A collectible power-up that floats down the road.
    # Disappears automatically after TIMEOUT frames if not collected.
    # Three kinds: nitro (speed), shield (protection), repair (clear obstacles).

    TIMEOUT = 8 * FPS   # disappears after 8 seconds if not collected
    # 8 seconds × 60 FPS = 480 frames.
    # Class-level constant shared by all PowerUp instances.

    def __init__(self, speed_ref: list, kind: str = None):
        # speed_ref: shared speed list.
        # kind:      if provided, forces this type; otherwise random.

        super().__init__()

        self._speed   = speed_ref

        self.kind     = kind or random.choice(POWERUP_TYPES)
        # Pick a random type from ["nitro", "shield", "repair"] unless one is specified.

        self.image    = self._make_surface()
        # Draw the power-up's visual (colored circle with a letter label).

        self.rect     = self.image.get_rect()

        self._timer   = self.TIMEOUT
        # Start the despawn countdown at 480 frames.
        # Counts down in move() each frame.

        self.rect.center = (
            random.choice(LANE_CENTERS),
            # Spawn in a random lane.
            random.randint(-200, -40),
            # Spawn between 40 and 200 pixels above the screen top.
            # The randomness staggers multiple potential spawns so they don't
            # all appear at the same time.
        )

    def _make_surface(self):
        # Creates the visual for this power-up: a colored circle with a letter.

        color = POWERUP_COLORS[self.kind]
        # Get the color for this power-up type (cyan/blue/green).

        surf  = pygame.Surface((28, 28), pygame.SRCALPHA)
        # 28×28 transparent surface to draw the circle onto.

        pygame.draw.circle(surf, color, (14, 14), 14)
        # Filled circle: center=(14,14) within the 28×28 surface, radius=14.
        # Fills the entire surface edge-to-edge.

        pygame.draw.circle(surf, WHITE, (14, 14), 14, 2)
        # 2px white border outline for visual definition.

        # Letter label
        font = pygame.font.SysFont("Verdana", 13, bold=True)
        # Create a bold Verdana font at size 13 for the label letter.
        # SysFont looks for the font installed on the OS; may fall back to default.

        lbl  = {"nitro": "N", "shield": "S", "repair": "R"}[self.kind]
        # Map the power-up kind to a single letter: N, S, or R.

        txt  = font.render(lbl, True, BLACK)
        # Render the letter as a Surface. True = anti-aliased edges. BLACK = text color.

        surf.blit(txt, txt.get_rect(center=(14, 14)))
        # Center the letter Surface on the circle Surface.
        # txt.get_rect(center=(14,14)) positions it perfectly in the middle.

        return surf

    def move(self):
        # Called every frame. Scrolls the power-up downward and handles auto-expiry.

        self.rect.move_ip(0, self._speed[0] * 0.5)
        # Power-ups move at 50% of road speed — slower than everything else
        # so the player has more time to react and collect them.

        self._timer -= 1
        # Count down the auto-despawn timer each frame.

        if self.rect.top > SCREEN_HEIGHT or self._timer <= 0:
            # Either: scrolled off-screen, or timer ran out (8 seconds elapsed).
            self.kill()
            # Remove this sprite from ALL groups it belongs to.
            # pygame handles the cleanup; no further references to it will be kept
            # by the groups, so it will be garbage-collected.


# ============================================================
#  Sprite: NitroStrip (road feature — speed-boost strip)
# ============================================================
class NitroStrip(pygame.sprite.Sprite):
    """Decorative road strip; treated as a power-up zone."""
    # A horizontal stripe painted across the full road width.
    # When the player drives over it, main.py detects the collision and applies
    # a temporary speed boost. The strip itself is purely visual + a collision trigger.

    def __init__(self, speed_ref: list):
        super().__init__()

        self._speed = speed_ref
        # Store speed reference for scrolling.

        self.image  = pygame.Surface((SCREEN_WIDTH, 18), pygame.SRCALPHA)
        # Full-width (400px) strip, 18px tall, with transparency support.

        for i in range(0, SCREEN_WIDTH, 20):
            pygame.draw.rect(self.image, (*NITRO_COLOR, 120), (i, 0, 10, 18))
        # Draw alternating 10px-wide cyan rectangles across the strip.
        # range(0, SCREEN_WIDTH, 20) = [0, 20, 40, ..., 380] — every 20px.
        # Each rect is 10px wide with a 10px gap, creating a dashed-line effect.
        # (*NITRO_COLOR, 120) = (0, 220, 255, 120) — cyan at ~47% opacity.
        # The semi-transparency lets the road show through, looking like paint on asphalt.

        self.rect = self.image.get_rect()
        # Create the bounding Rect.

        self.rect.centerx = SCREEN_WIDTH // 2
        # Center the strip horizontally (it's already full-width, so this = 200).

        self.rect.bottom   = -10
        # Place the strip just above the visible screen top; it scrolls down into view.

    def move(self):
        # Called every frame. Scrolls the strip downward at full road speed.

        self.rect.move_ip(0, self._speed[0])
        # Move at the same speed as the road so it appears "painted on" the asphalt.

        if self.rect.top > SCREEN_HEIGHT:
            # Strip has scrolled off the bottom of the screen.
            self.kill()
            # Destroy the sprite — unlike coins/enemies, nitro strips are one-shot.
            # A new one will be spawned by main.py's nitro_timer after a random delay.