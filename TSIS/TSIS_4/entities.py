"""
entities.py — All game entities: Snake, Food, PowerUp, Obstacle.
This file defines every "living" or interactive object that appears on the game board.
"""

# pygame: the game library used for drawing, input, timing, etc.
import pygame
# random: used to generate random positions and pick random power-up/food types
import random
# time: used to measure how long food/power-ups have been alive on the board
import time

# Import shared constants from config.py:
# Direction vectors (UP/DOWN/LEFT/RIGHT), cell size (CELL),
# screen dimensions, and all named colors.
from config import (
    UP, DOWN, LEFT, RIGHT, CELL,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    RED, BLUE, GOLD, DARK_RED, CYAN, ORANGE, PURPLE, WHITE,
)

# ---------------------------------------------------------------------------
# Snake
# ---------------------------------------------------------------------------

class Snake:
    # __init__ is called once when a new Snake object is created.
    # `color` is the body color, defaulting to white if none is given.
    def __init__(self, color=(255, 255, 255)):
        # The snake is stored as a list of (x, y) tuples — each tuple is one
        # body segment. The LAST item is always the head.
        # Starts as a 5-segment horizontal line at y=200.
        self.snake = [(200, 200), (210, 200), (220, 200), (230, 200), (240, 200)]

        # The snake starts moving to the RIGHT.
        self.direction = RIGHT

        # Build two pygame Surfaces for drawing: one for body, one for head.
        self.set_color(color)

        # Shield starts as inactive; becomes True when a shield power-up is collected.
        self.shield_active = False

    def set_color(self, color):
        # Creates a CELL×CELL square surface filled with the given color — used for body segments.
        self.skin = pygame.Surface((CELL, CELL))
        self.skin.fill(color)

        # Make the head slightly brighter by adding 40 to each RGB channel,
        # clamped at 255 so it never overflows.
        head_color = tuple(min(255, c + 40) for c in color)

        # Create a separate surface for the head, using the brighter color.
        self.head_skin = pygame.Surface((CELL, CELL))
        self.head_skin.fill(head_color)

    def crawl(self, grow=False, obstacles=None):
        """Move the snake one step. Returns True on success, False on collision."""

        # Unpack the current head position (last element of the list).
        head_x, head_y = self.snake[-1]

        # Calculate where the new head will be based on current direction.
        # Each direction shifts by exactly one CELL in the appropriate axis.
        if self.direction == RIGHT:
            new_head = (head_x + CELL, head_y)       # move right: increase X
        elif self.direction == LEFT:
            new_head = (head_x - CELL, head_y)       # move left: decrease X
        elif self.direction == UP:
            new_head = (head_x, head_y - CELL)       # move up: decrease Y (Y grows downward in pygame)
        elif self.direction == DOWN:
            new_head = (head_x, head_y + CELL)       # move down: increase Y

        # Check if the new head is outside the screen boundaries.
        border_hit = (
            new_head[0] < 0 or new_head[0] >= SCREEN_WIDTH or   # off left or right edge
            new_head[1] < 0 or new_head[1] >= SCREEN_HEIGHT      # off top or bottom edge
        )

        # Check if the new head lands on any existing body segment (self-collision).
        self_hit = new_head in self.snake

        # Check if the new head lands on any obstacle block (if obstacles were passed in).
        obs_hit = obstacles is not None and new_head in obstacles

        # If any collision was detected…
        if border_hit or self_hit or obs_hit:
            if self.shield_active:
                # Shield absorbs this one hit — deactivate it and skip the move.
                self.shield_active = False
                # Return True so the game doesn't end — the snake just freezes for one tick.
                return True
            # No shield: signal that the snake has died.
            return False

        # No collision — add the new head to the end of the body list.
        self.snake.append(new_head)

        if not grow:
            # Normal move: remove the tail segment so the snake stays the same length.
            self.snake.pop(0)
        # If grow=True, the tail is kept, making the snake one segment longer.

        # Movement was successful.
        return True

    def shorten(self, amount=2):
        """Remove segments from the tail. Returns False if snake becomes too short."""
        # Remove `amount` segments from the front (tail end) of the body list.
        for _ in range(amount):
            if len(self.snake) > 1:          # never remove the last segment (head)
                self.snake.pop(0)
        # Return False if the snake is now critically short (1 segment = just the head).
        return len(self.snake) > 1

    def draw(self, surface):
        # Draw every segment except the head using the body skin surface.
        for pos in self.snake[:-1]:          # slice excludes the last element (head)
            surface.blit(self.skin, pos)

        # Draw the head (last element) with the slightly brighter head skin.
        surface.blit(self.head_skin, self.snake[-1])


# ---------------------------------------------------------------------------
# Food
# ---------------------------------------------------------------------------

class Food:
    # TYPES defines the three food varieties as a list of tuples:
    # (min_chance_threshold, score_weight, color, lifetime_seconds, label)
    # Random number in [0,1) selects a type: >= 0.90 → golden, >= 0.70 → super, else normal.
    TYPES = [
        # (min_chance, weight, color, lifetime, label)
        (0.00, 1,  RED,      0,  "normal"),   # 70 % — red, no timer (lifetime=0 means it never expires)
        (0.70, 3,  BLUE,     10, "super"),    # 20 % — blue, disappears after 10 s
        (0.90, 5,  GOLD,     5,  "golden"),   # 10 % — gold, disappears after 5 s
    ]

    def __init__(self, snake_body, obstacles=None):
        # Default starting position; overwritten immediately by respawn().
        self.position = (0, 0)

        # Store obstacle positions so food doesn't spawn on top of them.
        self.obstacles = obstacles or set()

        # Place the food on the board for the first time.
        self.respawn(snake_body)

    def respawn(self, snake_body):
        # Roll a random float between 0.0 and 1.0 to pick food type.
        chance = random.random()

        # Iterate TYPES in reverse so the highest-threshold types are checked first.
        for min_c, w, col, lt, lbl in reversed(self.TYPES):
            if chance >= min_c:
                # Assign this food's properties from the matching type tuple.
                self.weight   = w      # score multiplier when eaten
                self.color    = col    # draw color
                self.lifetime = lt     # how many seconds before it vanishes (0 = forever)
                self.label    = lbl    # human-readable type name
                break                  # stop once a match is found

        # Find a free cell on the grid and set self.position.
        self._place(snake_body)

        # Record the exact moment this food appeared (used to check expiry).
        self.spawn_time = time.time()

    def _place(self, snake_body):
        # Build a set of all cells that are already occupied.
        blocked = set(snake_body) | self.obstacles

        # Keep trying random grid positions until a free one is found.
        while True:
            # Pick a random column aligned to the grid (multiples of CELL).
            x = random.randrange(0, SCREEN_WIDTH,  CELL)
            # Pick a random row aligned to the grid.
            y = random.randrange(0, SCREEN_HEIGHT, CELL)

            if (x, y) not in blocked:
                # Found a free cell — place food here and stop looping.
                self.position = (x, y)
                return

    def is_expired(self):
        # Normal food (lifetime == 0) never expires.
        if self.lifetime == 0:
            return False
        # For timed food: compare elapsed seconds to its lifetime limit.
        return (time.time() - self.spawn_time) > self.lifetime

    def draw(self, surface):
        # Draw the food square using its assigned color.
        pygame.draw.rect(surface, self.color, (*self.position, CELL, CELL))

        # Draw a tiny white 3×3 dot near the top-left corner to simulate a shine/highlight.
        pygame.draw.rect(surface, (255, 255, 255, 120),
                         (self.position[0] + 2, self.position[1] + 2, 3, 3))


# ---------------------------------------------------------------------------
# Poison Food
# ---------------------------------------------------------------------------

class PoisonFood:
    # Dark red color distinguishes poison from normal food.
    COLOR    = DARK_RED
    # Poison food disappears after 8 seconds if not eaten.
    LIFETIME = 8  # seconds

    def __init__(self, snake_body, obstacles=None):
        # Store obstacle positions to avoid spawning on them.
        self.obstacles = obstacles or set()

        # Default position; overwritten immediately by _place().
        self.position  = (0, 0)

        # Record when this poison appeared, used for expiry checks.
        self.spawn_time = time.time()

        # Find a valid free cell and set self.position.
        self._place(snake_body)

    def _place(self, snake_body):
        # Build the set of all occupied cells (body + obstacles).
        blocked = set(snake_body) | self.obstacles

        # Randomly search for a free grid-aligned cell.
        while True:
            x = random.randrange(0, SCREEN_WIDTH,  CELL)
            y = random.randrange(0, SCREEN_HEIGHT, CELL)
            if (x, y) not in blocked:
                self.position = (x, y)   # found a safe spot — use it
                return

    def is_expired(self):
        # Compare how many seconds have passed since spawn to the fixed LIFETIME.
        return (time.time() - self.spawn_time) > self.LIFETIME

    def draw(self, surface):
        # Draw the poison square in dark red.
        pygame.draw.rect(surface, self.COLOR, (*self.position, CELL, CELL))

        # Compute the pixel center of this cell.
        cx, cy = self.position[0] + CELL // 2, self.position[1] + CELL // 2

        # Draw a white "X" (two diagonal lines) to visually signal danger / skull crossbones.
        pygame.draw.line(surface, (255, 255, 255), (cx - 3, cy - 3), (cx + 3, cy + 3), 1)  # top-left → bottom-right
        pygame.draw.line(surface, (255, 255, 255), (cx + 3, cy - 3), (cx - 3, cy + 3), 1)  # top-right → bottom-left


# ---------------------------------------------------------------------------
# Power-up
# ---------------------------------------------------------------------------

class PowerUp:
    # How long (in milliseconds) a power-up sits on the board before disappearing.
    FIELD_LIFETIME_MS = 8000  # 8 seconds = 8000 ms

    # Dictionary mapping each power-up kind to its visual and gameplay properties.
    TYPES = {
        "speed_boost": {
            "color":    ORANGE,   # drawn in orange
            "label":    "SPEED",  # text shown in the HUD when active
            "duration": 5000,     # effect lasts 5 seconds (5000 ms) after being picked up
            "symbol":   ">",      # icon character (not currently drawn but available for use)
        },
        "slow_motion": {
            "color":    CYAN,     # drawn in cyan
            "label":    "SLOW",
            "duration": 5000,     # effect lasts 5 seconds
            "symbol":   "~",
        },
        "shield": {
            "color":    PURPLE,   # drawn in purple
            "label":    "SHIELD",
            "duration": 0,        # duration=0 means it lasts until it's actually triggered (absorbs one hit)
            "symbol":   "O",
        },
    }

    def __init__(self, snake_body, obstacles=None):
        # Store obstacle positions so the power-up doesn't spawn on a wall.
        self.obstacles   = obstacles or set()

        # Randomly select one of the three power-up types.
        self.kind        = random.choice(list(self.TYPES.keys()))

        # Store the property dictionary for the chosen type for quick access.
        self.info        = self.TYPES[self.kind]

        # Record the pygame tick count at spawn (used for millisecond-accurate expiry).
        self.spawn_ticks = pygame.time.get_ticks()

        # Find a free cell on the grid and set self.position.
        self._place(snake_body)

    def _place(self, snake_body):
        # Build the set of blocked cells (body + obstacles).
        blocked = set(snake_body) | self.obstacles

        # Search for a free grid-aligned cell.
        while True:
            x = random.randrange(0, SCREEN_WIDTH,  CELL)
            y = random.randrange(0, SCREEN_HEIGHT, CELL)
            if (x, y) not in blocked:
                self.position = (x, y)  # safe position found
                return

    def is_expired(self):
        # Check if the power-up has been on the field longer than FIELD_LIFETIME_MS.
        return (pygame.time.get_ticks() - self.spawn_ticks) > self.FIELD_LIFETIME_MS

    def draw(self, surface, font_small):
        # Draw the power-up square in its type-specific color.
        pygame.draw.rect(surface, self.info["color"], (*self.position, CELL, CELL))

        # Calculate how many milliseconds are left before the power-up disappears.
        elapsed      = pygame.time.get_ticks() - self.spawn_ticks
        remaining_ms = self.FIELD_LIFETIME_MS - elapsed

        # In the last 3 seconds, make the outline blink every 250 ms to warn the player.
        # `(elapsed // 250) % 2 == 0` alternates between True and False every 250 ms.
        if remaining_ms < 3000 and (elapsed // 250) % 2 == 0:
            # Draw a 1-pixel white border just outside the cell square when the blink is "on".
            pygame.draw.rect(surface, (255, 255, 255),
                             (self.position[0] - 1, self.position[1] - 1, CELL + 2, CELL + 2), 1)


# ---------------------------------------------------------------------------
# Obstacle
# ---------------------------------------------------------------------------

class Obstacle:
    # All obstacle blocks are drawn in this muted grey-blue color.
    COLOR = (100, 100, 110)

    def __init__(self, snake_body, existing_obstacles, food_positions):
        # A set of (x, y) grid positions that make up this obstacle cluster.
        self.blocks = set()

        # Generate the actual block positions, avoiding the snake and existing objects.
        self._generate(snake_body, existing_obstacles, food_positions)

    def _generate(self, snake_body, existing_obstacles, food_positions):
        """Place a cluster of wall blocks that don't trap the snake."""

        # Combine all currently occupied cells into one blocked set.
        blocked = set(snake_body) | existing_obstacles | food_positions

        # Build a "safe zone" — a 5-cell radius bubble around every snake segment.
        # Obstacles won't spawn inside this zone, preventing instant unfair deaths.
        safe = set()
        for (sx, sy) in snake_body:
            for dx in range(-5, 6):         # -5 to +5 cells in X
                for dy in range(-5, 6):     # -5 to +5 cells in Y
                    safe.add((sx + dx * CELL, sy + dy * CELL))

        # Randomly decide how many blocks this obstacle cluster will have (3–7).
        count    = random.randint(3, 7)
        attempts = 0  # safety counter to prevent infinite loops on a very crowded board

        # Keep placing blocks until we reach `count` or exhaust 200 attempts.
        while len(self.blocks) < count and attempts < 200:
            attempts += 1

            # Pick a random grid-aligned position anywhere on the screen.
            x   = random.randrange(0, SCREEN_WIDTH,  CELL)
            y   = random.randrange(0, SCREEN_HEIGHT, CELL)
            pos = (x, y)

            # Only place a block here if it's free, outside the safe zone, and not already part of this cluster.
            if pos not in blocked and pos not in safe and pos not in self.blocks:
                self.blocks.add(pos)    # add to this obstacle's block set
                blocked.add(pos)        # mark as occupied so later blocks don't stack here

    def draw(self, surface):
        # Draw each block in the cluster.
        for (x, y) in self.blocks:
            # Outer rectangle: the main wall color.
            pygame.draw.rect(surface, self.COLOR, (x, y, CELL, CELL))

            # Inner rectangle: slightly darker and inset by 2 px on each side.
            # This creates a subtle raised / 3-D bevel effect.
            pygame.draw.rect(surface, (60, 60, 70), (x + 2, y + 2, CELL - 4, CELL - 4))