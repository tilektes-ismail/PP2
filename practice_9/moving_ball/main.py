

import pygame
import sys
from ball import Ball


# ── Colors ─────────────────────────────────
WHITE      = (255, 255, 255)
LIGHT_GRAY = (245, 245, 245)
GRAY       = (180, 180, 180)
DARK_GRAY  = (60, 60, 60)
ACCENT     = (100, 160, 220)


def draw_grid(surface, width, height, step=40):
    """Draw a subtle grid for visual reference."""
    for x in range(0, width, step):
        pygame.draw.line(surface, (235, 235, 235), (x, 0), (x, height), 1)
    for y in range(0, height, step):
        pygame.draw.line(surface, (235, 235, 235), (0, y), (width, y), 1)


def draw_hud(surface, ball, font):
    """Draw position info at the bottom."""
    pygame.draw.rect(surface, DARK_GRAY, (0, surface.get_height() - 36, surface.get_width(), 36))
    info = f"Position: ({ball.x}, {ball.y})   |   Arrow keys to move   |   ESC to quit"
    text = font.render(info, True, (200, 200, 200))
    surface.blit(text, text.get_rect(center=(surface.get_width() // 2, surface.get_height() - 18)))


def main():
    pygame.init()

    SCREEN_WIDTH  = 600
    SCREEN_HEIGHT = 600
    FPS           = 60

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Moving Ball Game — Arrow Keys to Move")

    ball  = Ball(SCREEN_WIDTH, SCREEN_HEIGHT - 36)  # account for HUD
    clock = pygame.time.Clock()
    font  = pygame.font.SysFont("Arial", 14)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:
                    ball.move("up")
                elif event.key == pygame.K_DOWN:
                    ball.move("down")
                elif event.key == pygame.K_LEFT:
                    ball.move("left")
                elif event.key == pygame.K_RIGHT:
                    ball.move("right")

        # Draw
        screen.fill(WHITE)
        draw_grid(screen, SCREEN_WIDTH, SCREEN_HEIGHT - 36)
        ball.draw(screen)
        draw_hud(screen, ball, font)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
