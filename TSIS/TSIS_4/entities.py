"""
entities.py — All game entities: Snake, Food, PowerUp, Obstacle.
"""

import pygame
import random
import time

from config import (
    UP, DOWN, LEFT, RIGHT, CELL,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    RED, BLUE, GOLD, DARK_RED, CYAN, ORANGE, PURPLE, WHITE,
)

# ---------------------------------------------------------------------------
# Snake
# ---------------------------------------------------------------------------

class Snake:
    def __init__(self, color=(255, 255, 255)):
        self.snake = [(200, 200), (210, 200), (220, 200), (230, 200), (240, 200)]
        self.direction = RIGHT
        self.set_color(color)
        self.shield_active = False

    def set_color(self, color):
        self.skin = pygame.Surface((CELL, CELL))
        self.skin.fill(color)
        head_color = tuple(min(255, c + 40) for c in color)
        self.head_skin = pygame.Surface((CELL, CELL))
        self.head_skin.fill(head_color)

    def crawl(self, grow=False, obstacles=None):
        """Move the snake one step. Returns True on success, False on collision."""
        head_x, head_y = self.snake[-1]
        if self.direction == RIGHT:
            new_head = (head_x + CELL, head_y)
        elif self.direction == LEFT:
            new_head = (head_x - CELL, head_y)
        elif self.direction == UP:
            new_head = (head_x, head_y - CELL)
        elif self.direction == DOWN:
            new_head = (head_x, head_y + CELL)

        # Border collision
        border_hit = (
            new_head[0] < 0 or new_head[0] >= SCREEN_WIDTH or
            new_head[1] < 0 or new_head[1] >= SCREEN_HEIGHT
        )
        # Self collision
        self_hit = new_head in self.snake
        # Obstacle collision
        obs_hit = obstacles is not None and new_head in obstacles

        if border_hit or self_hit or obs_hit:
            if self.shield_active:
                # Shield absorbs the hit once
                self.shield_active = False
                # Just don't move this tick to avoid confusion
                return True
            return False

        self.snake.append(new_head)
        if not grow:
            self.snake.pop(0)
        return True

    def shorten(self, amount=2):
        """Remove segments from the tail. Returns False if snake becomes too short."""
        for _ in range(amount):
            if len(self.snake) > 1:
                self.snake.pop(0)
        return len(self.snake) > 1

    def draw(self, surface):
        for pos in self.snake[:-1]:
            surface.blit(self.skin, pos)
        surface.blit(self.head_skin, self.snake[-1])


# ---------------------------------------------------------------------------
# Food
# ---------------------------------------------------------------------------

class Food:
    TYPES = [
        # (min_chance, weight, color, lifetime, label)
        (0.00, 1,  RED,      0,  "normal"),   # 70 % — red, no timer
        (0.70, 3,  BLUE,     10, "super"),    # 20 % — blue, 10 s
        (0.90, 5,  GOLD,     5,  "golden"),   # 10 % — gold, 5 s
    ]

    def __init__(self, snake_body, obstacles=None):
        self.position = (0, 0)
        self.obstacles = obstacles or set()
        self.respawn(snake_body)

    def respawn(self, snake_body):
        chance = random.random()
        for min_c, w, col, lt, lbl in reversed(self.TYPES):
            if chance >= min_c:
                self.weight   = w
                self.color    = col
                self.lifetime = lt
                self.label    = lbl
                break

        self._place(snake_body)
        self.spawn_time = time.time()

    def _place(self, snake_body):
        blocked = set(snake_body) | self.obstacles
        while True:
            x = random.randrange(0, SCREEN_WIDTH,  CELL)
            y = random.randrange(0, SCREEN_HEIGHT, CELL)
            if (x, y) not in blocked:
                self.position = (x, y)
                return

    def is_expired(self):
        if self.lifetime == 0:
            return False
        return (time.time() - self.spawn_time) > self.lifetime

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (*self.position, CELL, CELL))
        # Small shine dot for visual clarity
        pygame.draw.rect(surface, (255, 255, 255, 120),
                         (self.position[0] + 2, self.position[1] + 2, 3, 3))


# ---------------------------------------------------------------------------
# Poison Food
# ---------------------------------------------------------------------------

class PoisonFood:
    COLOR    = DARK_RED
    LIFETIME = 8  # seconds

    def __init__(self, snake_body, obstacles=None):
        self.obstacles = obstacles or set()
        self.position  = (0, 0)
        self.spawn_time = time.time()
        self._place(snake_body)

    def _place(self, snake_body):
        blocked = set(snake_body) | self.obstacles
        while True:
            x = random.randrange(0, SCREEN_WIDTH,  CELL)
            y = random.randrange(0, SCREEN_HEIGHT, CELL)
            if (x, y) not in blocked:
                self.position = (x, y)
                return

    def is_expired(self):
        return (time.time() - self.spawn_time) > self.LIFETIME

    def draw(self, surface):
        pygame.draw.rect(surface, self.COLOR, (*self.position, CELL, CELL))
        # Skull-like cross mark
        cx, cy = self.position[0] + CELL // 2, self.position[1] + CELL // 2
        pygame.draw.line(surface, (255, 255, 255), (cx - 3, cy - 3), (cx + 3, cy + 3), 1)
        pygame.draw.line(surface, (255, 255, 255), (cx + 3, cy - 3), (cx - 3, cy + 3), 1)


# ---------------------------------------------------------------------------
# Power-up
# ---------------------------------------------------------------------------

class PowerUp:
    FIELD_LIFETIME_MS = 8000  # 8 seconds on field

    TYPES = {
        "speed_boost": {
            "color":    ORANGE,
            "label":    "SPEED",
            "duration": 5000,
            "symbol":   ">",
        },
        "slow_motion": {
            "color":    CYAN,
            "label":    "SLOW",
            "duration": 5000,
            "symbol":   "~",
        },
        "shield": {
            "color":    PURPLE,
            "label":    "SHIELD",
            "duration": 0,       # lasts until triggered
            "symbol":   "O",
        },
    }

    def __init__(self, snake_body, obstacles=None):
        self.obstacles   = obstacles or set()
        self.kind        = random.choice(list(self.TYPES.keys()))
        self.info        = self.TYPES[self.kind]
        self.spawn_ticks = pygame.time.get_ticks()
        self._place(snake_body)

    def _place(self, snake_body):
        blocked = set(snake_body) | self.obstacles
        while True:
            x = random.randrange(0, SCREEN_WIDTH,  CELL)
            y = random.randrange(0, SCREEN_HEIGHT, CELL)
            if (x, y) not in blocked:
                self.position = (x, y)
                return

    def is_expired(self):
        return (pygame.time.get_ticks() - self.spawn_ticks) > self.FIELD_LIFETIME_MS

    def draw(self, surface, font_small):
        pygame.draw.rect(surface, self.info["color"], (*self.position, CELL, CELL))
        # Blinking outline when about to expire
        elapsed = pygame.time.get_ticks() - self.spawn_ticks
        remaining_ms = self.FIELD_LIFETIME_MS - elapsed
        if remaining_ms < 3000 and (elapsed // 250) % 2 == 0:
            pygame.draw.rect(surface, (255, 255, 255),
                             (self.position[0] - 1, self.position[1] - 1, CELL + 2, CELL + 2), 1)


# ---------------------------------------------------------------------------
# Obstacle
# ---------------------------------------------------------------------------

class Obstacle:
    COLOR = (100, 100, 110)

    def __init__(self, snake_body, existing_obstacles, food_positions):
        self.blocks = set()
        self._generate(snake_body, existing_obstacles, food_positions)

    def _generate(self, snake_body, existing_obstacles, food_positions):
        """Place a cluster of wall blocks that don't trap the snake."""
        blocked = set(snake_body) | existing_obstacles | food_positions
        # Safety margin: protect a 5-cell radius around each snake segment
        safe = set()
        for (sx, sy) in snake_body:
            for dx in range(-5, 6):
                for dy in range(-5, 6):
                    safe.add((sx + dx * CELL, sy + dy * CELL))

        count = random.randint(3, 7)
        attempts = 0
        while len(self.blocks) < count and attempts < 200:
            attempts += 1
            x = random.randrange(0, SCREEN_WIDTH,  CELL)
            y = random.randrange(0, SCREEN_HEIGHT, CELL)
            pos = (x, y)
            if pos not in blocked and pos not in safe and pos not in self.blocks:
                self.blocks.add(pos)
                blocked.add(pos)

    def draw(self, surface):
        for (x, y) in self.blocks:
            pygame.draw.rect(surface, self.COLOR, (x, y, CELL, CELL))
            # Inner darker square for 3-D look
            pygame.draw.rect(surface, (60, 60, 70), (x + 2, y + 2, CELL - 4, CELL - 4))
