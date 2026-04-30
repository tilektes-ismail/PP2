"""
game.py — Core game loop (one play-through).
Returns (score, level) when the game ends.
This file contains the entire logic for a single game session:
input handling, movement, collision detection, scoring, leveling up, and drawing.
"""

# pygame: the game library for graphics, input events, and timing
import pygame
# random: used to decide whether to spawn poison food or a power-up after eating
import random
# time: used to calculate how many seconds remain on timed food items
import time

# Import shared constants from config.py
from config import (
    CELL,                          # pixel size of one grid square
    SCREEN_WIDTH, SCREEN_HEIGHT,   # total canvas dimensions in pixels
    FOOD_PER_LEVEL,                # how many foods the player must eat to advance a level
    INITIAL_SPEED,                 # starting game speed (ticks per second / FPS)
    BLACK, GRAY, GOLD, WHITE, RED, CYAN, ORANGE, PURPLE,  # named color tuples
)
# Import all game entity classes from entities.py
from entities import Snake, Food, PoisonFood, PowerUp, Obstacle


# Probability (0–1) that a PoisonFood spawns each time normal food is eaten.
# 0.30 = 30% chance.
POISON_SPAWN_CHANCE  = 0.30

# Probability (0–1) that a PowerUp spawns each time food is eaten.
# 0.35 = 35% chance.
POWERUP_SPAWN_CHANCE = 0.35


def run_game(screen, clock, fonts, settings, player_id, personal_best):
    """
    Run one game session.
    Returns (score, level_reached).

    Parameters:
        screen        — the main pygame display surface to draw onto
        clock         — pygame.time.Clock used to cap the frame rate
        fonts         — dict of pre-loaded font objects keyed by size name
        settings      — dict of user preferences (snake color, grid overlay, etc.)
        player_id     — identifier for the current player (used externally for save data)
        personal_best — the player's all-time high score, displayed in the HUD
    """

    # Pull out the two font sizes we'll need for HUD text rendering.
    font_sm   = fonts["small"]    # small font: used for HUD labels and timers
    font_med  = fonts["medium"]   # medium font: available for bigger messages if needed

    # Read snake color from settings; default to white if the key is missing.
    # settings stores colors as lists [R, G, B] so we convert to a tuple for pygame.
    snake_color = tuple(settings.get("snake_color", [255, 255, 255]))

    # Read whether the grid overlay should be drawn (default True).
    show_grid   = settings.get("grid_overlay", True)

    # ---- State ----
    # Game speed in frames per second — increases by 2 each level-up.
    speed  = INITIAL_SPEED

    # Current level number; starts at 1.
    level  = 1

    # Running total of points scored this session.
    score  = 0

    # Counter for foods eaten within the current level; resets on level-up.
    foods_eaten_in_lvl = 0

    # Create the player's snake with the chosen color.
    snake     = Snake(color=snake_color)

    # A flat set of (x, y) tuples for every obstacle block on the board.
    # Passed to snake.crawl() and entity spawners to prevent overlap.
    obstacles = set()

    # Spawn the first food item, avoiding the snake's starting body.
    food      = Food(snake.snake, obstacles)

    # Poison food slot — None means no poison is on the board right now.
    poison    = None   # PoisonFood | None

    # Power-up slot — None means no power-up is on the board right now.
    powerup   = None   # PowerUp | None

    # Name of the currently active power-up effect, or None if none is active.
    # Possible values: "speed_boost", "slow_motion", "shield", None
    active_effect        = None

    # The pygame tick count (ms since start) when the current effect was activated.
    # Used to calculate how much time remains on timed effects.
    effect_start_ticks   = 0

    # How long the current effect lasts in milliseconds.
    effect_duration_ms   = 0

    def all_obstacle_positions():
        # Simple helper that returns the obstacle set.
        # Using a function keeps the call site readable and makes it easy
        # to extend later (e.g., add dynamic obstacles).
        return obstacles

    def _draw_grid():
        # Draw faint vertical lines across the full screen height, spaced by CELL pixels.
        for x in range(0, SCREEN_WIDTH, CELL):
            pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))

        # Draw faint horizontal lines across the full screen width, spaced by CELL pixels.
        for y in range(0, SCREEN_HEIGHT, CELL):
            pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))

    def _draw_hud():
        # ---- Score and level row ----
        # Build a progress string like "(3/5)" showing foods eaten vs foods needed.
        lvl_prog = f"({foods_eaten_in_lvl}/{FOOD_PER_LEVEL})"

        # Render the combined score/level string in gold and blit it to the top-left corner.
        hud = font_sm.render(f"Score: {score}   Lvl: {level} {lvl_prog}", True, GOLD)
        screen.blit(hud, (5, 5))   # 5px from left and top edges

        # ---- Personal best row ----
        # Show the all-time high score in grey just below the main HUD line.
        pb = font_sm.render(f"PB: {personal_best}", True, (180, 180, 180))
        screen.blit(pb, (5, 22))   # 22px from top = directly below first row

        # ---- Food countdown timer (only for timed food types) ----
        if food.lifetime > 0:
            # Calculate remaining seconds: lifetime minus elapsed seconds since spawn.
            rem = int(food.lifetime - (time.time() - food.spawn_time))

            if rem >= 0:   # don't show negative values if drawing is slightly delayed
                # Render the remaining time in the top-right corner.
                t = font_sm.render(f"Bonus: {rem}s", True, WHITE)
                screen.blit(t, (SCREEN_WIDTH - t.get_width() - 5, 5))

        # ---- Shield indicator ----
        # Show "SHIELD" in purple when the snake has an active shield.
        if snake.shield_active:
            sh = font_sm.render("SHIELD", True, PURPLE)
            # Position just below the food timer in the top-right area.
            screen.blit(sh, (SCREEN_WIDTH - sh.get_width() - 5, 22))

        # ---- Active timed effect countdown ----
        # Shield has no timer (lasts until triggered), so skip it here.
        if active_effect and active_effect != "shield":
            # How many milliseconds have passed since the effect was activated.
            elapsed = pygame.time.get_ticks() - effect_start_ticks

            # Convert remaining ms to whole seconds; clamp to 0 so it never goes negative.
            rem_eff = max(0, (effect_duration_ms - elapsed) // 1000)

            # Orange for speed boost, cyan for slow motion.
            col   = ORANGE if active_effect == "speed_boost" else CYAN
            label = "FAST"  if active_effect == "speed_boost" else "SLOW"

            # Render the label + remaining seconds and place it below the shield text slot.
            eff_txt = font_sm.render(f"{label}: {rem_eff}s", True, col)
            screen.blit(eff_txt, (SCREEN_WIDTH - eff_txt.get_width() - 5, 39))

    # ---- Main loop ----
    # `running` controls whether the game is still active.
    # Setting it to False anywhere in the loop exits cleanly after the current tick.
    running = True

    while running:
        # Cap the loop to `speed` frames per second; speed increases with each level.
        clock.tick(speed)

        # Snapshot the current time in milliseconds for consistent comparisons this tick.
        now_ticks = pygame.time.get_ticks()

        # ---- Event handling ----
        for event in pygame.event.get():
            # Window close button → cleanly quit pygame and exit the process.
            if event.type == pygame.QUIT:
                pygame.quit()
                import sys; sys.exit()

            if event.type == pygame.KEYDOWN:
                # Arrow key controls — the `and snake.direction != X` checks prevent
                # the snake from reversing directly into itself (instant death).
                # Direction values: UP=0, DOWN=1, LEFT=2, RIGHT=3 (from config.py).

                if   event.key == pygame.K_UP    and snake.direction != 1: snake.direction = 0   # can't go UP if currently going DOWN (1)
                elif event.key == pygame.K_DOWN  and snake.direction != 0: snake.direction = 1   # can't go DOWN if currently going UP (0)
                elif event.key == pygame.K_LEFT  and snake.direction != 3: snake.direction = 2   # can't go LEFT if currently going RIGHT (3)
                elif event.key == pygame.K_RIGHT and snake.direction != 2: snake.direction = 3   # can't go RIGHT if currently going LEFT (2)

                elif event.key == pygame.K_ESCAPE:
                    # ESC key: immediately end this session and return to the main menu.
                    return score, level

        # ---- Expire active timed power-up effect ----
        # Shield is excluded because it has no time limit — it expires on hit, not on a timer.
        if active_effect and active_effect != "shield":
            if (now_ticks - effect_start_ticks) >= effect_duration_ms:
                # Undo the speed change that was applied when this effect was activated.
                if active_effect == "speed_boost":
                    # Speed was increased by 4 when boost was picked up — reduce it back.
                    # max() prevents speed from going below the base speed.
                    speed = max(INITIAL_SPEED, speed - 4)
                elif active_effect == "slow_motion":
                    # Speed was decreased by 3 when slow was picked up — increase it back.
                    speed = max(INITIAL_SPEED, speed + 3)

                # Clear the active effect now that it has worn off.
                active_effect = None

        # ---- Expire field items that have been on the board too long ----

        # If the current food item's timer ran out, replace it with a fresh one.
        if food.is_expired():
            food.respawn(snake.snake)

        # If poison food's 8-second timer expired, remove it from the board.
        if poison and poison.is_expired():
            poison = None

        # If the power-up's 8-second field timer expired, remove it from the board.
        if powerup and powerup.is_expired():
            powerup = None

        # ---- Move the snake one step ----
        # head_before is saved (though not currently used after this line)
        # in case we need it for interpolation or effects later.
        head_before = snake.snake[-1]

        # crawl() returns False if the snake collided with a wall, itself, or an obstacle.
        # grow=False means the tail is removed each tick (standard movement).
        if not snake.crawl(grow=False, obstacles=all_obstacle_positions()):
            # Collision with no shield — game over, exit the loop.
            running = False
            break

        # The head position after the move — used for all collision checks below.
        new_head = snake.snake[-1]

        # ---- Check if food was eaten ----
        if new_head == food.position:
            # Insert an extra segment at the tail position to grow the snake by 1.
            # snake.snake[0] is the current tail; duplicating it before the move
            # effectively makes the snake one cell longer.
            snake.snake.insert(0, snake.snake[0])

            # Add points: base 10 × food weight (1 for normal, 3 for super, 5 for golden).
            score += 10 * food.weight

            # Count this food toward the level-up threshold.
            foods_eaten_in_lvl += 1

            # ---- Check for level-up ----
            if foods_eaten_in_lvl >= FOOD_PER_LEVEL:
                level += 1                  # advance to the next level
                foods_eaten_in_lvl = 0      # reset the per-level food counter
                speed += 2                  # increase game speed by 2 FPS

                # Starting from level 3, add a new obstacle cluster to the board.
                if level >= 3:
                    obs = Obstacle(
                        snake.snake,
                        obstacles,
                        # Pass current food and poison positions so obstacles
                        # don't spawn directly on top of existing items.
                        {food.position} | ({poison.position} if poison else set()),
                    )
                    # Merge the new obstacle's block positions into the main obstacle set.
                    obstacles.update(obs.blocks)

            # Respawn food at a new random position, avoiding the snake and obstacles.
            food.respawn(snake.snake)

            # Roll to potentially spawn poison food (only if none is on the board).
            if poison is None and random.random() < POISON_SPAWN_CHANCE:
                poison = PoisonFood(snake.snake, obstacles)

            # Roll to potentially spawn a power-up (only if none is on the board).
            if powerup is None and random.random() < POWERUP_SPAWN_CHANCE:
                powerup = PowerUp(snake.snake, obstacles)

        # ---- Check if poison was eaten ----
        if poison and new_head == poison.position:
            # shorten() removes 2 tail segments; returns False if the snake is now too short to continue.
            if not snake.shorten(2):
                running = False   # snake is too short → game over
                break
            # Remove the poison from the board regardless of outcome.
            poison = None

        # ---- Check if power-up was collected ----
        if powerup and new_head == powerup.position:
            # Read the kind before clearing the reference.
            kind    = powerup.kind
            # Remove the power-up from the board immediately.
            powerup = None

            if kind == "speed_boost":
                speed += 4                          # increase FPS by 4 for the boost duration
                active_effect      = "speed_boost"  # mark the effect as active
                effect_start_ticks = now_ticks       # record when the effect started
                effect_duration_ms = 5000            # effect lasts 5 000 ms (5 seconds)

            elif kind == "slow_motion":
                speed = max(2, speed - 3)           # decrease FPS by 3, minimum of 2 so the game doesn't freeze
                active_effect      = "slow_motion"
                effect_start_ticks = now_ticks
                effect_duration_ms = 5000            # effect lasts 5 000 ms (5 seconds)

            elif kind == "shield":
                # Shield has no duration — it just sits on the snake until a collision triggers it.
                snake.shield_active = True
                active_effect = "shield"             # track it so the HUD can show the indicator

        # ---- Draw frame ----
        # Clear the entire screen to black before drawing the new frame.
        screen.fill(BLACK)

        # Optionally draw the grid lines over the black background.
        if show_grid:
            _draw_grid()

        # Draw each obstacle block manually (instead of using Obstacle.draw())
        # because obstacles is a flat set of positions, not a list of Obstacle objects.
        for (x, y) in obstacles:
            from config import CELL as C   # re-import CELL locally (same value as module-level CELL)
            pygame.draw.rect(screen, (100, 100, 110), (x, y, C, C))           # outer grey square
            pygame.draw.rect(screen, (60, 60, 70),   (x + 2, y + 2, C - 4, C - 4))  # inner darker square for bevel effect

        # Draw food, poison (if present), and power-up (if present).
        food.draw(screen)

        if poison:
            poison.draw(screen)         # dark red square with white X

        if powerup:
            powerup.draw(screen, font_sm)   # colored square with optional blinking outline

        # Draw the snake on top of all other objects.
        snake.draw(screen)

        # Draw HUD text (score, level, timers) on top of everything.
        _draw_hud()

        # Push the completed frame to the display (double-buffer swap).
        pygame.display.update()

    # Loop exited — either collision or ESC.
    # Return the final score and highest level reached to the caller (e.g., main menu).
    return score, level