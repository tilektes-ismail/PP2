# ============================================================
#  main.py  —  Car Dodge Game (Entry Point)
#
#  Run this file to start the game:
#      python main.py
#
#  All sprite classes and constants live in sprites.py.
#  This file handles:
#    - Pygame initialisation
#    - Sprite / group setup
#    - The main game loop (events, HUD, collisions, game-over)
# ============================================================

import pygame, sys
from pygame.locals import QUIT
import time
import os

# Import everything we need from our sprites module
from sprites import (
    BASE_DIR,
    # Colours used in HUD / game-over screen
    BLACK, WHITE, RED, YELLOW, SILVER_COLOR,
    # Screen & timing
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    # Difficulty knobs
    INITIAL_SPEED, COIN_SPEED_MILESTONE, COIN_SPEED_BOOST, TIME_SPEED_BOOST,
    # Sprite classes
    Player, Enemy, Coin,
)

# ============================================================
#  Pygame + Mixer Initialisation
# ============================================================
pygame.init()
pygame.mixer.init()

# ============================================================
#  Shared Mutable State
# ============================================================
# We wrap SPEED and SCORE in single-element lists so sprite classes
# (Enemy, Coin) can read and write them without needing 'global'.
# main.py reads them as speed[0] and score[0].
speed = [INITIAL_SPEED]   # [0] = current fall speed
score = [0]               # [0] = enemies dodged

COINS          = 0                      # Total coin points collected
_next_milestone = COIN_SPEED_MILESTONE  # Next coin threshold for speed boost

# ============================================================
#  Display
# ============================================================
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
DISPLAYSURF.fill(WHITE)
pygame.display.set_caption("Car Dodge — Extended")

# ============================================================
#  Assets
# ============================================================
background = pygame.image.load(os.path.join(BASE_DIR, "images", "AnimatedStreet.png"))

# ============================================================
#  Fonts
# ============================================================
font        = pygame.font.SysFont("Verdana", 60)
font_small  = pygame.font.SysFont("Verdana", 20)
game_over_surf = font.render("Game Over", True, BLACK)

# ============================================================
#  Music
# ============================================================
pygame.mixer.music.load(os.path.join(BASE_DIR, "music", "background.wav"))
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)   # -1 = loop forever

# ============================================================
#  Sprite Setup
# ============================================================
# Pass the shared speed/score lists so sprites always use the live values
P1 = Player()
E1 = Enemy(speed_ref=speed, score_ref=score)

# One coin on screen at a time — increase range() for more simultaneous coins
coin_list = [Coin(speed_ref=speed) for _ in range(1)]

# Sprite groups
enemies     = pygame.sprite.Group(E1)
coins       = pygame.sprite.Group(*coin_list)
all_sprites = pygame.sprite.Group(P1, E1, *coin_list)

# ============================================================
#  Custom Timer Event
# ============================================================
# Fires every 1 000 ms to apply the time-based speed increase
INC_SPEED = pygame.USEREVENT + 1
pygame.time.set_timer(INC_SPEED, 1000)

# ============================================================
#  Clock
# ============================================================
FramePerSec = pygame.time.Clock()


# ============================================================
#  Helper — Coin Milestone Speed Boost  (Feature 2)
# ============================================================
def check_coin_milestone():
    """Boost speed whenever collected coins reach the next milestone.

    Each milestone advances by COIN_SPEED_MILESTONE points, so boosts
    fire at 10 → 20 → 30 … coin-points.  This runs alongside the
    time-based boost, so heavy coin collection makes the game harder faster.
    """
    global _next_milestone
    if COINS >= _next_milestone:
        speed[0]        += COIN_SPEED_BOOST
        _next_milestone += COIN_SPEED_MILESTONE   # schedule the next boost


# ============================================================
#  HUD Drawing Helper
# ============================================================
def draw_hud():
    """Render score, coin count, and next-milestone indicator each frame."""
    # Score — top-left
    score_surf = font_small.render("Score: " + str(score[0]), True, BLACK)
    DISPLAYSURF.blit(score_surf, (10, 10))

    # Coin count — top-right
    coin_surf = font_small.render("C: " + str(COINS), True, YELLOW)
    DISPLAYSURF.blit(coin_surf, (SCREEN_WIDTH - 60, 10))

    # Next boost threshold — top-right, second line
    next_surf = font_small.render("Next: " + str(_next_milestone), True, BLACK)
    DISPLAYSURF.blit(next_surf, (SCREEN_WIDTH - 80, 30))

    # Coin legend — bottom of screen so the player always knows tier values
    legend = [
        ("● Bronze = 1pt", (205, 127, 50)),
        ("● Silver = 3pt", BLACK),
        ("● Gold   = 5pt", YELLOW),
    ]
    for i, (text, color) in enumerate(legend):
        surf = font_small.render(text, True, color)
        DISPLAYSURF.blit(surf, (10, SCREEN_HEIGHT - 60 + i * 20))


# ============================================================
#  Game Over Screen
# ============================================================
def show_game_over():
    """Play crash sound, display the game-over screen, then quit."""
    pygame.mixer.music.stop()
    pygame.mixer.Sound(os.path.join(BASE_DIR, "music", "crash.wav")).play()
    time.sleep(1)

    DISPLAYSURF.fill(RED)
    DISPLAYSURF.blit(game_over_surf, (30, 250))

    # Final stats: score + coins collected
    final = font_small.render(
        "Score: " + str(score[0]) + "   Coins: " + str(COINS), True, BLACK
    )
    DISPLAYSURF.blit(final, (90, 350))

    pygame.display.update()

    # Kill all sprites, pause briefly, then exit cleanly
    for entity in all_sprites:
        entity.kill()
    time.sleep(2)
    pygame.quit()
    sys.exit()


# ============================================================
#  Main Game Loop
# ============================================================
while True:

    # ---- Event Handling ----
    for event in pygame.event.get():
        if event.type == INC_SPEED:
            # Time-based difficulty ramp: +0.5 speed every second
            speed[0] += TIME_SPEED_BOOST
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    # ---- Draw Background ----
    DISPLAYSURF.blit(background, (0, 0))

    # ---- Draw HUD ----
    draw_hud()

    # ---- Move + Draw All Sprites ----
    for entity in all_sprites:
        entity.move()
        DISPLAYSURF.blit(entity.image, entity.rect)

    # ---- Coin Collection (Feature 1 + 2) ----
    collected = pygame.sprite.spritecollide(P1, coins, False)  # type: ignore
    for coin in collected:
        COINS += coin.value    # Bronze=1, Silver=3, Gold=5
        check_coin_milestone() # check if a speed boost should fire
        coin._respawn()        # recycle coin with a new random tier

    # ---- Enemy Collision → Game Over ----
    if pygame.sprite.spritecollideany(P1, enemies):  # type: ignore
        show_game_over()       # this function does not return (calls sys.exit)

    # ---- Refresh Display & Cap FPS ----
    pygame.display.update()
    FramePerSec.tick(FPS)
