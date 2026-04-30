import pygame       # Pygame library for graphics and surfaces
import random       # random.random() and random.randrange() for food placement
import time         # time.time() to track food spawn timestamps

# Direction constants — stored as integers for easy comparison
UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3

CELL = 10                           # Size of one grid cell in pixels (snake moves in 10px steps)
SCREEN_WIDTH, SCREEN_HEIGHT = 400, 400  # Total window size in pixels

class Snake:
    def __init__(self):
        # Initial snake body — list of (x, y) tuples, tail first, head last
        self.snake = [(200, 200), (210, 200), (220, 200), (230, 200), (240, 200)]
        self.direction = RIGHT          # Snake starts moving to the right

        self.skin = pygame.Surface((CELL, CELL))    # Create a 10x10 surface for body segments
        self.skin.fill((255, 255, 255))             # Fill body segments white

        self.head_skin = pygame.Surface((CELL, CELL))   # Separate 10x10 surface for the head
        self.head_skin.fill((200, 200, 200))            # Head is slightly darker grey to distinguish it

    def crawl(self, grow=False):
        head_x, head_y = self.snake[-1]             # Get current head position (last element = head)

        # Calculate where the new head will be based on current direction
        if self.direction == RIGHT: new_head = (head_x + CELL, head_y)     # Move one cell right
        elif self.direction == LEFT: new_head = (head_x - CELL, head_y)    # Move one cell left
        elif self.direction == UP: new_head = (head_x, head_y - CELL)      # Move one cell up
        elif self.direction == DOWN: new_head = (head_x, head_y + CELL)    # Move one cell down

        # Collision check — return False (game over) if new head hits a wall or the snake itself
        if (new_head[0] < 0 or new_head[0] >= SCREEN_WIDTH or     # Hit left or right wall
            new_head[1] < 0 or new_head[1] >= SCREEN_HEIGHT or    # Hit top or bottom wall
            new_head in self.snake):                                # Head overlaps body
            return False

        self.snake.append(new_head)         # Add new head position to the end of the list
        if not grow: self.snake.pop(0)      # Remove tail only if not growing (keeps length the same)
        return True                         # Movement was successful


class Food:
    def __init__(self, snake_body):
        self.position = (0, 0)      # Placeholder position before first respawn
        self.respawn(snake_body)    # Immediately place food at a valid random location

    def respawn(self, snake_body):
        chance = random.random()    # Random float between 0.0 and 1.0 for weighted food type selection

        # 70% chance — normal food: low value, stays forever
        if chance < 0.7:
            self.weight, self.color, self.lifetime = 1, (255, 0, 0), 0     # weight=1pt, red, no expiry

        # 20% chance — super food: medium value, disappears after 10 seconds
        elif chance < 0.9:
            self.weight, self.color, self.lifetime = 3, (0, 0, 255), 10    # weight=3pt, blue, 10s timer

        # 10% chance — golden food: high value, disappears after 5 seconds
        else:
            self.weight, self.color, self.lifetime = 5, (255, 215, 0), 5   # weight=5pt, gold, 5s timer

        # Keep trying random positions until we find one not occupied by the snake
        while True:
            x = random.randrange(0, SCREEN_WIDTH, CELL)     # Random X snapped to grid
            y = random.randrange(0, SCREEN_HEIGHT, CELL)    # Random Y snapped to grid
            if (x, y) not in snake_body:                    # Make sure it doesn't overlap the snake
                self.position = (x, y)                      # Accept this position
                break                                       # Exit the loop

        self.spawn_time = time.time()   # Record the exact moment this food appeared

    def is_expired(self):
        """Check if the food has disappeared due to time running out."""
        if self.lifetime == 0: return False                         # Normal food never expires
        return (time.time() - self.spawn_time) > self.lifetime      # True if time elapsed exceeds lifetime

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (*self.position, CELL, CELL))  # Draw a filled 10x10 square at food's position