import pygame
from pygame.locals import K_UP, K_DOWN, K_LEFT, K_RIGHT, QUIT, KEYDOWN, K_q
import sys
import random

# -------------------- CONSTANTS --------------------
UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3

GAME_ON = True

# Screen and grid settings
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 400
CELL = 10  # Each snake/food block is 10x10 pixels

# Starting speed and level
SPEED = 10
LEVEL = 1
SCORE = 0
FOOD_PER_LEVEL = 3  # Foods needed to advance to next level
FOODS_EATEN = 0     # Track how many foods eaten in current level

# Colors
BLACK  = (0,   0,   0)
WHITE  = (255, 255, 255)
RED    = (255, 0,   0)
GREEN  = (0,   200, 0)
YELLOW = (255, 215, 0)
GRAY   = (40,  40,  40)

# -------------------- SNAKE CLASS --------------------
class Snake():

    def __init__(self):
        # Snake starts as a list of (x, y) positions
        self.snake = [(200, 200), (210, 200), (220, 200), (230, 200), (240, 200)]

        # White body block
        self.skin = pygame.Surface((CELL, CELL))
        self.skin.fill(WHITE)

        # Gray head block (slightly different color)
        self.head = pygame.Surface((CELL, CELL))
        self.head.fill((200, 200, 200))

        self.direction = RIGHT

    def crawl(self, grow=False):
        """
        Move snake one step in current direction.
        If grow=True, don't remove tail (snake gets longer).
        Returns False if snake hits a wall or itself.
        """
        head_x, head_y = self.snake[-1]

        new_head = (head_x, head_y)

        # Calculate new head position based on direction
        if self.direction == RIGHT:
            new_head = (head_x + CELL, head_y)
        elif self.direction == LEFT:
            new_head = (head_x - CELL, head_y)
        elif self.direction == UP:
            new_head = (head_x, head_y - CELL)
        elif self.direction == DOWN:
            new_head = (head_x, head_y + CELL)

        # ← ADDED: Check wall collision
        if (new_head[0] < 0 or new_head[0] >= SCREEN_WIDTH or
                new_head[1] < 0 or new_head[1] >= SCREEN_HEIGHT):
            return False  # Snake hit the wall → game over

        # ← ADDED: Check self collision (hit own body)
        if new_head in self.snake:
            return False  # Snake hit itself → game over

        # Add new head
        self.snake.append(new_head)

        # ← ADDED: Only remove tail if not growing
        if not grow:
            self.snake.pop(0)

        return True  # Snake is alive


# -------------------- FOOD CLASS --------------------
# ← ADDED: Food class that spawns at random valid positions
class Food():

    def __init__(self, snake_body):
        self.color = RED
        # Generate first food position
        self.position = self.random_position(snake_body)

        # Red food block
        self.image = pygame.Surface((CELL, CELL))
        self.image.fill(self.color)

    def random_position(self, snake_body):
        """
        Generate a random position that:
        - Is on the grid (multiples of CELL)
        - Does not overlap with the snake body
        """
        while True:
            x = random.randrange(0, SCREEN_WIDTH, CELL)
            y = random.randrange(0, SCREEN_HEIGHT, CELL)
            # Only use position if it's not on the snake
            if (x, y) not in snake_body:
                return (x, y)

    def respawn(self, snake_body):
        """Move food to a new random valid position after being eaten."""
        self.position = self.random_position(snake_body)


# -------------------- SETUP --------------------
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake Game")
clock = pygame.time.Clock()

# Fonts for score and level display
font = pygame.font.SysFont("Verdana", 16)
font_big = pygame.font.SysFont("Verdana", 40)

snake = Snake()

# ← ADDED: Create first food avoiding snake's starting position
food = Food(snake.snake)


# -------------------- HELPER FUNCTIONS --------------------
def draw_grid():
    """Draw subtle grid lines on the background."""
    for x in range(0, SCREEN_WIDTH, CELL):
        pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, CELL):
        pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))

def show_game_over():
    """Display game over screen with final score and level."""
    screen.fill(BLACK)
    go_text = font_big.render("GAME OVER", True, RED)
    score_text = font.render(f"Score: {SCORE}   Level: {LEVEL}", True, WHITE)
    restart_text = font.render("Press Q to quit", True, GRAY)
    screen.blit(go_text, (SCREEN_WIDTH//2 - go_text.get_width()//2, 140))
    screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 210))
    screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, 260))
    pygame.display.update()

    # Wait for Q key to quit
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_q:
                    pygame.quit()
                    sys.exit()


# -------------------- GAME LOOP --------------------
while GAME_ON:
    clock.tick(SPEED)

    # Handle input events
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

        if event.type == KEYDOWN:
            # Change direction but prevent reversing
            if event.key == K_UP and snake.direction != DOWN:
                snake.direction = UP
            elif event.key == K_LEFT and snake.direction != RIGHT:
                snake.direction = LEFT
            elif event.key == K_DOWN and snake.direction != UP:
                snake.direction = DOWN
            elif event.key == K_RIGHT and snake.direction != LEFT:
                snake.direction = RIGHT

    # ← ADDED: Check if snake eats food this step
    grow = snake.snake[-1] == food.position

    # Move snake (grow if food eaten)
    alive = snake.crawl(grow=grow)

    # ← ADDED: Stop game if snake dies
    if not alive:
        GAME_ON = False
        show_game_over()
        break

    # ← ADDED: If food was eaten, update score and respawn food
    if grow:
        SCORE += 10
        FOODS_EATEN += 1
        food.respawn(snake.snake)

        # ← ADDED: Level up after eating FOOD_PER_LEVEL foods
        if FOODS_EATEN >= FOOD_PER_LEVEL:
            LEVEL += 1
            FOODS_EATEN = 0         # Reset food counter for new level
            SPEED += 2              # ← ADDED: Increase speed each level
            clock.tick(SPEED)       # Apply new speed immediately

    # -------------------- DRAWING --------------------
    screen.fill(BLACK)

    # ← ADDED: Draw subtle grid
    draw_grid()

    # Draw snake body (all except last = head)
    for snake_pos in snake.snake[:-1]:
        screen.blit(snake.skin, snake_pos)

    # Draw snake head
    screen.blit(snake.head, snake.snake[-1])

    # ← ADDED: Draw food
    screen.blit(food.image, food.position)

    # ← ADDED: Draw score and level counters at top
    score_text = font.render(f"Score: {SCORE}", True, YELLOW)
    level_text = font.render(f"Level: {LEVEL}", True, YELLOW)
    foods_text = font.render(f"Food: {FOODS_EATEN}/{FOOD_PER_LEVEL}", True, YELLOW)

    screen.blit(score_text, (5, 5))
    screen.blit(level_text, (SCREEN_WIDTH//2 - level_text.get_width()//2, 5))
    screen.blit(foods_text, (SCREEN_WIDTH - foods_text.get_width() - 5, 5))

    pygame.display.update()

pygame.quit()