"""
game.py — Core game loop (one play-through).
Returns (score, level) when the game ends.
"""

import pygame
import random
import time

from config import (
    CELL, SCREEN_WIDTH, SCREEN_HEIGHT,
    FOOD_PER_LEVEL, INITIAL_SPEED,
    BLACK, GRAY, GOLD, WHITE, RED, CYAN, ORANGE, PURPLE,
)
from entities import Snake, Food, PoisonFood, PowerUp, Obstacle


# Chance to spawn poison food each time normal food is eaten
POISON_SPAWN_CHANCE  = 0.30
# Chance to spawn a power-up each time food is eaten
POWERUP_SPAWN_CHANCE = 0.35


def run_game(screen, clock, fonts, settings, player_id, personal_best):
    """
    Run one game session.
    Returns (score, level_reached).
    """
    font_sm   = fonts["small"]
    font_med  = fonts["medium"]

    snake_color = tuple(settings.get("snake_color", [255, 255, 255]))
    show_grid   = settings.get("grid_overlay", True)

    # ---- State ----
    speed  = INITIAL_SPEED
    level  = 1
    score  = 0
    foods_eaten_in_lvl = 0

    snake     = Snake(color=snake_color)
    obstacles = set()  # flat set of blocked positions

    food      = Food(snake.snake, obstacles)
    poison    = None   # PoisonFood | None
    powerup   = None   # PowerUp | None

    # Active power-up effect
    active_effect        = None   # "speed_boost" | "slow_motion" | "shield" | None
    effect_start_ticks   = 0
    effect_duration_ms   = 0

    def all_obstacle_positions():
        return obstacles

    def _draw_grid():
        for x in range(0, SCREEN_WIDTH, CELL):
            pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, CELL):
            pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))

    def _draw_hud():
        # Score / level
        lvl_prog = f"({foods_eaten_in_lvl}/{FOOD_PER_LEVEL})"
        hud = font_sm.render(f"Score: {score}   Lvl: {level} {lvl_prog}", True, GOLD)
        screen.blit(hud, (5, 5))
        # Personal best
        pb = font_sm.render(f"PB: {personal_best}", True, (180, 180, 180))
        screen.blit(pb, (5, 22))
        # Food timer
        if food.lifetime > 0:
            rem = int(food.lifetime - (time.time() - food.spawn_time))
            if rem >= 0:
                t = font_sm.render(f"Bonus: {rem}s", True, WHITE)
                screen.blit(t, (SCREEN_WIDTH - t.get_width() - 5, 5))
        # Shield indicator
        if snake.shield_active:
            sh = font_sm.render("SHIELD", True, PURPLE)
            screen.blit(sh, (SCREEN_WIDTH - sh.get_width() - 5, 22))
        # Active effect timer
        if active_effect and active_effect != "shield":
            elapsed = pygame.time.get_ticks() - effect_start_ticks
            rem_eff = max(0, (effect_duration_ms - elapsed) // 1000)
            col = ORANGE if active_effect == "speed_boost" else CYAN
            label = "FAST" if active_effect == "speed_boost" else "SLOW"
            eff_txt = font_sm.render(f"{label}: {rem_eff}s", True, col)
            screen.blit(eff_txt, (SCREEN_WIDTH - eff_txt.get_width() - 5, 39))

    # ---- Main loop ----
    running = True
    while running:
        clock.tick(speed)
        now_ticks = pygame.time.get_ticks()

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                import sys; sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP    and snake.direction != 1: snake.direction = 0
                elif event.key == pygame.K_DOWN  and snake.direction != 0: snake.direction = 1
                elif event.key == pygame.K_LEFT  and snake.direction != 3: snake.direction = 2
                elif event.key == pygame.K_RIGHT and snake.direction != 2: snake.direction = 3
                elif event.key == pygame.K_ESCAPE:
                    return score, level  # back to menu

        # Expire active power-up effect
        if active_effect and active_effect != "shield":
            if (now_ticks - effect_start_ticks) >= effect_duration_ms:
                # Restore speed
                if active_effect == "speed_boost":
                    speed = max(INITIAL_SPEED, speed - 4)
                elif active_effect == "slow_motion":
                    speed = max(INITIAL_SPEED, speed + 3)
                active_effect = None

        # Expire field items
        if food.is_expired():
            food.respawn(snake.snake)

        if poison and poison.is_expired():
            poison = None

        if powerup and powerup.is_expired():
            powerup = None

        # Move
        head_before = snake.snake[-1]
        if not snake.crawl(grow=False, obstacles=all_obstacle_positions()):
            running = False
            break

        # Check food eaten
        new_head = snake.snake[-1]
        if new_head == food.position:
            # Grow
            snake.snake.insert(0, snake.snake[0])  # add to tail
            score += 10 * food.weight
            foods_eaten_in_lvl += 1

            # Level up?
            if foods_eaten_in_lvl >= FOOD_PER_LEVEL:
                level += 1
                foods_eaten_in_lvl = 0
                speed += 2
                # Add obstacles from level 3 onward
                if level >= 3:
                    obs = Obstacle(
                        snake.snake,
                        obstacles,
                        {food.position} | ({poison.position} if poison else set()),
                    )
                    obstacles.update(obs.blocks)

            food.respawn(snake.snake)

            # Maybe spawn poison
            if poison is None and random.random() < POISON_SPAWN_CHANCE:
                poison = PoisonFood(snake.snake, obstacles)

            # Maybe spawn power-up
            if powerup is None and random.random() < POWERUP_SPAWN_CHANCE:
                powerup = PowerUp(snake.snake, obstacles)

        # Check poison eaten
        if poison and new_head == poison.position:
            if not snake.shorten(2):
                running = False
                break
            poison = None

        # Check power-up collected
        if powerup and new_head == powerup.position:
            kind = powerup.kind
            powerup = None
            if kind == "speed_boost":
                speed += 4
                active_effect      = "speed_boost"
                effect_start_ticks = now_ticks
                effect_duration_ms = 5000
            elif kind == "slow_motion":
                speed = max(2, speed - 3)
                active_effect      = "slow_motion"
                effect_start_ticks = now_ticks
                effect_duration_ms = 5000
            elif kind == "shield":
                snake.shield_active = True
                active_effect = "shield"

        # ---- Draw ----
        screen.fill(BLACK)
        if show_grid:
            _draw_grid()

        # Obstacles
        for (x, y) in obstacles:
            from config import CELL as C
            pygame.draw.rect(screen, (100, 100, 110), (x, y, C, C))
            pygame.draw.rect(screen, (60, 60, 70), (x + 2, y + 2, C - 4, C - 4))

        food.draw(screen)
        if poison:
            poison.draw(screen)
        if powerup:
            powerup.draw(screen, font_sm)

        snake.draw(screen)
        _draw_hud()

        pygame.display.update()

    return score, level
