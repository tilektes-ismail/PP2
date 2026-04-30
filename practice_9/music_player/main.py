import pygame
import os
from player import MusicPlayer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
music_path = os.path.join(BASE_DIR, "music")

player = MusicPlayer(music_path)
pygame.init()

WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Music Player")

# Colors
BG = (18, 18, 18)
WHITE = (255, 255, 255)
GRAY = (180, 180, 180)
ACCENT = (0, 200, 150)

font_big = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 28)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
music_path = os.path.join(BASE_DIR, "music")

player = MusicPlayer(music_path)

clock = pygame.time.Clock()
running = True


def draw_progress_bar(x, y, w, h):
    pygame.draw.rect(screen, GRAY, (x, y, w, h), 2)

    if player.is_playing:
        pos = pygame.mixer.music.get_pos() / 1000  # seconds
        progress = min(pos / 180, 1)  # fake 3 min track
        pygame.draw.rect(screen, ACCENT, (x, y, w * progress, h))


def draw():
    screen.fill(BG)

    # Title
    title = font_big.render("Music Player", True, WHITE)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 30))

    # Track name
    track = player.get_current_track()
    track_text = font_small.render(track, True, GRAY)
    screen.blit(track_text, (WIDTH//2 - track_text.get_width()//2, 120))

    # Progress bar
    draw_progress_bar(100, 180, 400, 10)

    # Controls (visual only)
    controls = "[P] Play   [S] Stop   [N] Next   [B] Back   [Q] Quit"
    ctrl_text = font_small.render(controls, True, GRAY)
    screen.blit(ctrl_text, (WIDTH//2 - ctrl_text.get_width()//2, 300))

    pygame.display.flip()


while running:
    clock.tick(60)
    draw()

    # auto next track
    if player.is_playing and not pygame.mixer.music.get_busy():
        player.next_track()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                player.play()

            elif event.key == pygame.K_s:
                player.stop()

            elif event.key == pygame.K_n:
                player.next_track()

            elif event.key == pygame.K_b:
                player.prev_track()

            elif event.key == pygame.K_q:
                running = False

pygame.quit()