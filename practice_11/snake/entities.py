import pygame
import random
import time

# Constants
UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3
CELL = 10
SCREEN_WIDTH, SCREEN_HEIGHT = 400, 400

class Snake:
    def __init__(self):
        self.snake = [(200, 200), (210, 200), (220, 200), (230, 200), (240, 200)]
        self.direction = RIGHT
        self.skin = pygame.Surface((CELL, CELL))
        self.skin.fill((255, 255, 255)) 
        self.head_skin = pygame.Surface((CELL, CELL))
        self.head_skin.fill((200, 200, 200))

    def crawl(self, grow=False):
        head_x, head_y = self.snake[-1]
        if self.direction == RIGHT: new_head = (head_x + CELL, head_y)
        elif self.direction == LEFT: new_head = (head_x - CELL, head_y)
        elif self.direction == UP: new_head = (head_x, head_y - CELL)
        elif self.direction == DOWN: new_head = (head_x, head_y + CELL)

        if (new_head[0] < 0 or new_head[0] >= SCREEN_WIDTH or
            new_head[1] < 0 or new_head[1] >= SCREEN_HEIGHT or
            new_head in self.snake):
            return False

        self.snake.append(new_head)
        if not grow: self.snake.pop(0)
        return True

class Food:
    def __init__(self, snake_body):
        self.position = (0, 0)
        self.respawn(snake_body)

    def respawn(self, snake_body):
        chance = random.random()
        
        # Weighted selection logic
        if chance < 0.7:
            # NORMAL FOOD (Red)
            self.weight, self.color, self.lifetime = 1, (255, 0, 0), 0 
        elif chance < 0.9:
            # SUPER FOOD (Blue) - Updated to 10 seconds
            self.weight, self.color, self.lifetime = 3, (0, 0, 255), 10 
        else:
            # GOLDEN FOOD (Gold) - Updated to 5 seconds
            self.weight, self.color, self.lifetime = 5, (255, 215, 0), 5 

        # Find a spot not covered by the snake
        while True:
            x = random.randrange(0, SCREEN_WIDTH, CELL)
            y = random.randrange(0, SCREEN_HEIGHT, CELL)
            if (x, y) not in snake_body:
                self.position = (x, y)
                break
        
        self.spawn_time = time.time()

    def is_expired(self):
        """Check if the food has disappeared due to time running out."""
        if self.lifetime == 0: return False
        return (time.time() - self.spawn_time) > self.lifetime

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (*self.position, CELL, CELL))