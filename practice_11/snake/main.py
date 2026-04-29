import pygame
import sys
import time
from pygame.locals import *
from entities import Snake, Food, SCREEN_WIDTH, SCREEN_HEIGHT, CELL

# --- SETUP ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake: Weighted Food Edition")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Verdana", 14)
font_big = pygame.font.SysFont("Verdana", 30)

# Colors
GRAY = (30, 30, 30) # Subtle color for grid lines

# --- GAME STATE ---
SPEED, LEVEL, SCORE = 5, 1, 0
FOOD_PER_LEVEL = 3
FOODS_EATEN_IN_LVL = 0

snake = Snake()
food = Food(snake.snake)

def draw_grid():
    """Draws subtle grid lines to help with navigation."""
    for x in range(0, SCREEN_WIDTH, CELL):
        pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, CELL):
        pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))

def show_game_over():
    screen.fill((0, 0, 0))
    msg = font_big.render("GAME OVER", True, (255, 0, 0))
    stat_msg = font.render(f"Final Score: {SCORE} | Level: {LEVEL}", True, (255, 255, 255))
    exit_msg = font.render("Press Q to Quit", True, (100, 100, 100))
    
    screen.blit(msg, (SCREEN_WIDTH//2 - msg.get_width()//2, 140))
    screen.blit(stat_msg, (SCREEN_WIDTH//2 - stat_msg.get_width()//2, 200))
    screen.blit(exit_msg, (SCREEN_WIDTH//2 - exit_msg.get_width()//2, 250))
    
    pygame.display.update()
    while True:
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); sys.exit()
            if event.type == KEYDOWN and event.key == K_q: pygame.quit(); sys.exit()

# --- MAIN LOOP ---
while True:
    clock.tick(SPEED)
    
    for event in pygame.event.get():
        if event.type == QUIT: pygame.quit(); sys.exit()
        if event.type == KEYDOWN:
            if event.key == K_UP and snake.direction != 1: snake.direction = 0
            elif event.key == K_DOWN and snake.direction != 0: snake.direction = 1
            elif event.key == K_LEFT and snake.direction != 3: snake.direction = 2
            elif event.key == K_RIGHT and snake.direction != 2: snake.direction = 3

    if food.is_expired():
        food.respawn(snake.snake)

    is_food_eaten = (snake.snake[-1] == food.position)
    if not snake.crawl(grow=is_food_eaten):
        show_game_over()

    if is_food_eaten:
        SCORE += (10 * food.weight)
        FOODS_EATEN_IN_LVL += 1
        if FOODS_EATEN_IN_LVL >= FOOD_PER_LEVEL:
            LEVEL += 1
            FOODS_EATEN_IN_LVL = 0
            SPEED += 2
        food.respawn(snake.snake)

    # --- DRAWING ---
    screen.fill((0, 0, 0)) # Clear background
    
    draw_grid() # Draw grid BEFORE snake and food
    
    food.draw(screen)
    
    for pos in snake.snake[:-1]: 
        screen.blit(snake.skin, pos)
    screen.blit(snake.head_skin, snake.snake[-1])
    
    # HUD
    level_progress = f"({FOODS_EATEN_IN_LVL}/{FOOD_PER_LEVEL})"
    hud_text = font.render(f"Score: {SCORE}   Lvl: {LEVEL} {level_progress}", True, (255, 215, 0))
    screen.blit(hud_text, (5, 5))
    
    if food.lifetime > 0:
        remaining = int(food.lifetime - (time.time() - food.spawn_time))
        if remaining >= 0:
            timer_txt = font.render(f"Bonus: {remaining}s left", True, (255, 255, 255))
            screen.blit(timer_txt, (5, 25))

    pygame.display.update()