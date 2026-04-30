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

import pygame, sys          # Pygame for graphics/events, sys for sys.exit()
from pygame.locals import QUIT  # QUIT constant for the window-close event
import time                 # time.sleep() for pause before game over screen
import os                   # os.path for building file paths to assets

# Import constants and sprite classes from our own sprites module
from sprites import (
    BASE_DIR,               # Absolute path to the project folder (for loading assets)
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
pygame.init()           # Start all Pygame modules (display, events, fonts, etc.)
pygame.mixer.init()     # Start the audio mixer separately so sounds can play

# ============================================================
#  Shared Mutable State
# ============================================================
# speed and score are single-element lists so sprite classes can modify them
# without needing 'global' — any code holding the list sees the updated value.
speed = [INITIAL_SPEED]   # speed[0] = how fast enemies/coins fall
score = [0]               # score[0] = number of enemies successfully dodged

COINS          = 0                      # Running total of coin points collected this session
_next_milestone = COIN_SPEED_MILESTONE  # Coin point threshold that triggers the next speed boost

# ============================================================
#  Display
# ============================================================
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))  # Create the game window
DISPLAYSURF.fill(WHITE)                                                 # Fill with white before first frame
pygame.display.set_caption("Car Dodge — Extended")                     # Set the title bar text

# ============================================================
#  Assets
# ============================================================
# Load the scrolling road background image from the images subfolder
background = pygame.image.load(os.path.join(BASE_DIR, "images", "AnimatedStreet.png"))

# ============================================================
#  Fonts
# ============================================================
font        = pygame.font.SysFont("Verdana", 60)    # Large font for "Game Over" text
font_small  = pygame.font.SysFont("Verdana", 20)    # Small font for HUD stats
game_over_surf = font.render("Game Over", True, BLACK)  # Pre-render "Game Over" so it's ready instantly

# ============================================================
#  Music
# ============================================================
pygame.mixer.music.load(os.path.join(BASE_DIR, "music", "background.wav"))  # Load background music file
pygame.mixer.music.set_volume(0.5)   # Set volume to 50% so it's not too loud
pygame.mixer.music.play(-1)          # Start playing; -1 means loop forever

# ============================================================
#  Sprite Setup
# ============================================================
P1 = Player()                               # Create the player car sprite
E1 = Enemy(speed_ref=speed, score_ref=score)  # Enemy reads speed[0] and writes score[0]

# Create coin sprites — increase range() number for more coins on screen at once
coin_list = [Coin(speed_ref=speed) for _ in range(1)]  # Currently one coin at a time

# Group containing only the enemy — used for collision detection
enemies     = pygame.sprite.Group(E1)
# Group containing all coins — used for coin collection detection
coins       = pygame.sprite.Group(*coin_list)
# Group containing every sprite — used to update and draw all at once
all_sprites = pygame.sprite.Group(P1, E1, *coin_list)

# ============================================================
#  Custom Timer Event
# ============================================================
INC_SPEED = pygame.USEREVENT + 1            # Define a unique event ID for our timer
pygame.time.set_timer(INC_SPEED, 1000)      # Fire INC_SPEED into the event queue every 1000ms (1 second)

# ============================================================
#  Clock
# ============================================================
FramePerSec = pygame.time.Clock()   # Clock object used to cap the frame rate


# ============================================================
#  Helper — Coin Milestone Speed Boost  (Feature 2)
# ============================================================
def check_coin_milestone():
    """Boost speed whenever collected coins reach the next milestone."""
    global _next_milestone                          # We need to modify the module-level variable
    if COINS >= _next_milestone:                    # Check if collected coins hit the threshold
        speed[0]        += COIN_SPEED_BOOST         # Increase fall speed by the boost amount
        _next_milestone += COIN_SPEED_MILESTONE     # Advance threshold to the next multiple


# ============================================================
#  HUD Drawing Helper
# ============================================================
def draw_hud():
    """Render score, coin count, and next-milestone indicator each frame."""
    # Render current score and draw it in the top-left corner
    score_surf = font_small.render("Score: " + str(score[0]), True, BLACK)
    DISPLAYSURF.blit(score_surf, (10, 10))

    # Render total coin points and draw in the top-right corner
    coin_surf = font_small.render("C: " + str(COINS), True, YELLOW)
    DISPLAYSURF.blit(coin_surf, (SCREEN_WIDTH - 60, 10))

    # Render next speed-boost threshold just below the coin counter
    next_surf = font_small.render("Next: " + str(_next_milestone), True, BLACK)
    DISPLAYSURF.blit(next_surf, (SCREEN_WIDTH - 80, 30))

    # Coin tier legend at the bottom so the player knows each coin's value
    legend = [
        ("● Bronze = 1pt", (205, 127, 50)),   # Bronze colour with 1 point label
        ("● Silver = 3pt", BLACK),             # Silver (shown in black text) with 3 points
        ("● Gold   = 5pt", YELLOW),            # Gold colour with 5 points
    ]
    for i, (text, color) in enumerate(legend):         # Loop through each legend entry
        surf = font_small.render(text, True, color)     # Render the label in its tier colour
        DISPLAYSURF.blit(surf, (10, SCREEN_HEIGHT - 60 + i * 20))  # Stack entries 20px apart near bottom


# ============================================================
#  Game Over Screen
# ============================================================
def show_game_over():
    """Play crash sound, display the game-over screen, then quit."""
    pygame.mixer.music.stop()                                                       # Stop background music
    pygame.mixer.Sound(os.path.join(BASE_DIR, "music", "crash.wav")).play()        # Play crash sound effect
    time.sleep(1)                                                                   # Wait 1 second for sound to play

    DISPLAYSURF.fill(RED)                           # Paint the screen red as game-over background
    DISPLAYSURF.blit(game_over_surf, (30, 250))     # Draw the pre-rendered "Game Over" text

    # Render and draw the final score + coins on the game-over screen
    final = font_small.render(
        "Score: " + str(score[0]) + "   Coins: " + str(COINS), True, BLACK
    )
    DISPLAYSURF.blit(final, (90, 350))      # Position stats below the "Game Over" heading

    pygame.display.update()                 # Push the game-over frame to the monitor

    # Remove every sprite from memory
    for entity in all_sprites:
        entity.kill()                       # kill() removes the sprite from all groups

    time.sleep(2)       # Hold the game-over screen for 2 seconds before closing
    pygame.quit()       # Shut down all Pygame modules
    sys.exit()          # Terminate the Python process


# ============================================================
#  Main Game Loop
# ============================================================
while True:

    # ---- Event Handling ----
    for event in pygame.event.get():            # Process every queued event this frame
        if event.type == INC_SPEED:             # Our custom 1-second timer fired
            speed[0] += TIME_SPEED_BOOST        # Increase fall speed slightly every second
        if event.type == QUIT:                  # User clicked the window's X button
            pygame.quit()
            sys.exit()

    # ---- Draw Background ----
    DISPLAYSURF.blit(background, (0, 0))        # Draw road background at top-left, covering last frame

    # ---- Draw HUD ----
    draw_hud()                                  # Render score, coins, and legend on top of background

    # ---- Move + Draw All Sprites ----
    for entity in all_sprites:                  # Loop through player, enemy, and all coins
        entity.move()                           # Call each sprite's movement logic
        DISPLAYSURF.blit(entity.image, entity.rect)  # Draw the sprite at its current position

    # ---- Coin Collection (Feature 1 + 2) ----
    # spritecollide returns a list of coins whose rect overlaps with P1's rect
    collected = pygame.sprite.spritecollide(P1, coins, False)   # False = don't auto-remove coins
    for coin in collected:                      # Handle each collected coin
        COINS += coin.value                     # Add coin's point value (1, 3, or 5) to total
        check_coin_milestone()                  # Check if this pushes us past a speed threshold
        coin._respawn()                         # Recycle the coin with a new random position and tier

    # ---- Enemy Collision → Game Over ----
    if pygame.sprite.spritecollideany(P1, enemies):  # Returns the enemy sprite if touching player
        show_game_over()                        # This never returns — calls sys.exit() internally

    # ---- Refresh Display & Cap FPS ----
    pygame.display.update()                     # Push the completed frame to the monitor
    FramePerSec.tick(FPS)                       # Wait so the loop runs at most FPS times per second