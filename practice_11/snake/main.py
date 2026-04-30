import pygame                        # Pygame library for window, graphics, and events
import sys                           # sys.exit() to terminate the program cleanly
import time                          # time.time() to calculate food timer countdowns
from pygame.locals import *          # Imports event/key constants like QUIT, KEYDOWN, K_UP, etc.
from entities import Snake, Food, SCREEN_WIDTH, SCREEN_HEIGHT, CELL  # Import game objects and screen size

# --- SETUP ---
pygame.init()                                                   # Initialize all Pygame modules
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)) # Create the game window (400x400)
pygame.display.set_caption("Snake: Weighted Food Edition")      # Set the window title bar text
clock = pygame.time.Clock()                                     # Clock used to control game speed
font = pygame.font.SysFont("Verdana", 14)                       # Small font for HUD and stats text
font_big = pygame.font.SysFont("Verdana", 30)                   # Large font for "GAME OVER" heading

# Colors
GRAY = (30, 30, 30)     # Very dark grey — subtle enough to show grid without distracting

# --- GAME STATE ---
SPEED, LEVEL, SCORE = 5, 1, 0   # Starting speed (ticks/sec), level, and score
FOOD_PER_LEVEL = 3               # How many food items must be eaten to advance one level
FOODS_EATEN_IN_LVL = 0           # Counter that resets each time the player levels up

snake = Snake()                  # Create the snake starting in the middle of the screen
food  = Food(snake.snake)        # Place the first food item, avoiding the snake's starting body


def draw_grid():
    """Draws subtle grid lines to help with navigation."""
    for x in range(0, SCREEN_WIDTH, CELL):                              # Step through every column
        pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))     # Draw a vertical line at each column
    for y in range(0, SCREEN_HEIGHT, CELL):                             # Step through every row
        pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))      # Draw a horizontal line at each row


def show_game_over():
    screen.fill((0, 0, 0))      # Clear the screen with black for the game over background

    # Render all three text surfaces
    msg      = font_big.render("GAME OVER", True, (255, 0, 0))                         # Big red heading
    stat_msg = font.render(f"Final Score: {SCORE} | Level: {LEVEL}", True, (255, 255, 255))  # White stats line
    exit_msg = font.render("Press Q to Quit", True, (100, 100, 100))                   # Grey quit hint

    # Center each text surface horizontally by subtracting half its width from the screen center
    screen.blit(msg,      (SCREEN_WIDTH//2 - msg.get_width()//2,      140))
    screen.blit(stat_msg, (SCREEN_WIDTH//2 - stat_msg.get_width()//2, 200))
    screen.blit(exit_msg, (SCREEN_WIDTH//2 - exit_msg.get_width()//2, 250))

    pygame.display.update()     # Push the game over frame to the monitor

    # Freeze here — wait for the player to quit, nothing else should happen
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:                              # Window X button clicked
                pygame.quit(); sys.exit()
            if event.type == KEYDOWN and event.key == K_q:     # Q key pressed
                pygame.quit(); sys.exit()


# --- MAIN LOOP ---
while True:
    clock.tick(SPEED)       # Pause so the loop runs exactly SPEED times per second (controls snake speed)

    for event in pygame.event.get():    # Process all events that happened since last frame
        if event.type == QUIT:          # Window X button — exit immediately
            pygame.quit(); sys.exit()
        if event.type == KEYDOWN:       # A key was just pressed
            # Change direction only if not reversing — prevents the snake from colliding with itself
            if   event.key == K_UP    and snake.direction != 1: snake.direction = 0  # Not already going DOWN
            elif event.key == K_DOWN  and snake.direction != 0: snake.direction = 1  # Not already going UP
            elif event.key == K_LEFT  and snake.direction != 3: snake.direction = 2  # Not already going RIGHT
            elif event.key == K_RIGHT and snake.direction != 2: snake.direction = 3  # Not already going LEFT

    if food.is_expired():               # Timed food (blue/gold) has run out before being eaten
        food.respawn(snake.snake)       # Replace it with a fresh randomly chosen food item

    # Check BEFORE moving: if head is already on food, the snake should grow this step
    is_food_eaten = (snake.snake[-1] == food.position)

    if not snake.crawl(grow=is_food_eaten):     # Move snake; returns False on wall or self collision
        show_game_over()                        # Collision detected — show game over screen (doesn't return)

    if is_food_eaten:
        SCORE += (10 * food.weight)             # Add points: 10 × food weight (1, 3, or 5)
        FOODS_EATEN_IN_LVL += 1                 # Increment the within-level food counter

        if FOODS_EATEN_IN_LVL >= FOOD_PER_LEVEL:   # Eaten enough food to level up
            LEVEL += 1                              # Advance to the next level
            FOODS_EATEN_IN_LVL = 0                  # Reset counter for the new level
            SPEED += 2                              # Increase snake speed by 2 ticks/sec

        food.respawn(snake.snake)       # Spawn a new food item after the current one was eaten

    # --- DRAWING ---
    screen.fill((0, 0, 0))     # Wipe last frame — fill with black before redrawing everything

    draw_grid()                # Draw grid lines first so snake and food appear on top

    food.draw(screen)          # Draw the food square at its current position

    for pos in snake.snake[:-1]:            # Loop through every body segment except the head
        screen.blit(snake.skin, pos)        # Draw body tile at each segment's position
    screen.blit(snake.head_skin, snake.snake[-1])   # Draw the head tile at the last (head) position

    # HUD — score and level progress bar text
    level_progress = f"({FOODS_EATEN_IN_LVL}/{FOOD_PER_LEVEL})"    # e.g. "(2/3)" shows progress to next level
    hud_text = font.render(f"Score: {SCORE}   Lvl: {LEVEL} {level_progress}", True, (255, 215, 0))
    screen.blit(hud_text, (5, 5))           # Draw HUD in the top-left corner

    # Countdown timer — only shown for timed food (blue/gold), not for normal food (lifetime == 0)
    if food.lifetime > 0:
        remaining = int(food.lifetime - (time.time() - food.spawn_time))    # Seconds left before expiry
        if remaining >= 0:                                                   # Don't show if already negative
            timer_txt = font.render(f"Bonus: {remaining}s left", True, (255, 255, 255))
            screen.blit(timer_txt, (5, 25))     # Draw countdown just below the main HUD line

    pygame.display.update()     # Push the fully drawn frame to the monitor