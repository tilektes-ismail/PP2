

import pygame


class Ball:
   

    RADIUS = 25
    DIAMETER = RADIUS * 2  
    STEP = 20              # pixels per key press
    COLOR = (220, 50, 50)
    OUTLINE = (160, 20, 20)

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Start at center
        self.x = screen_width // 2
        self.y = screen_height // 2

    def move(self, direction):
        
        new_x, new_y = self.x, self.y

        if direction == "up":
            new_y -= self.STEP
        elif direction == "down":
            new_y += self.STEP
        elif direction == "left":
            new_x -= self.STEP
        elif direction == "right":
            new_x += self.STEP

        # Boundary check — ignore move if ball would go off-screen
        if (self.RADIUS <= new_x <= self.screen_width - self.RADIUS and
                self.RADIUS <= new_y <= self.screen_height - self.RADIUS):
            self.x = new_x
            self.y = new_y
        # else: silently ignore (as per requirements)

    def draw(self, surface):
        """Draw the ball with a subtle 3D highlight effect."""
        # Shadow
        pygame.draw.circle(surface, (180, 180, 180),
                           (self.x + 3, self.y + 3), self.RADIUS)
        # Main ball
        pygame.draw.circle(surface, self.COLOR, (self.x, self.y), self.RADIUS)
        # Outline
        pygame.draw.circle(surface, self.OUTLINE, (self.x, self.y), self.RADIUS, 2)
        # Highlight (small white circle top-left)
        pygame.draw.circle(surface, (255, 150, 150),
                           (self.x - 8, self.y - 8), 7)
