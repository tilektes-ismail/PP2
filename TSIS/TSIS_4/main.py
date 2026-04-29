"""
main.py — Entry point. Manages all screens and the game loop.
Screens: Main Menu → Game → Game Over → Leaderboard / Settings.
"""

import pygame
import sys

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BLACK, WHITE, GOLD, RED, GRAY, DARK_GRAY,
    SCREEN_MENU, SCREEN_GAME, SCREEN_GAMEOVER, SCREEN_LEADERBOARD, SCREEN_SETTINGS,
)
import db
import settings as sett_mod
from game import run_game

# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake — TSIS 4")
clock  = pygame.time.Clock()

# Fonts
font_sm  = pygame.font.SysFont("Consolas", 13)
font_med = pygame.font.SysFont("Consolas", 18)
font_big = pygame.font.SysFont("Consolas", 32, bold=True)
fonts    = {"small": font_sm, "medium": font_med, "big": font_big}

# Try to initialize DB (graceful fallback if unavailable)
db_available = db.init_db()

# Load settings
settings = sett_mod.load_settings()

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def draw_bg():
    screen.fill((8, 8, 12))
    # Subtle scanline-style horizontal lines
    for y in range(0, SCREEN_HEIGHT, 4):
        pygame.draw.line(screen, (12, 12, 18), (0, y), (SCREEN_WIDTH, y))


def draw_text_center(text, font, color, y):
    surf = font.render(text, True, color)
    screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, y))


def draw_button(label, font, rect, active=False):
    """Draw a retro button. Returns True if mouse is hovering."""
    mx, my = pygame.mouse.get_pos()
    hovered = rect.collidepoint(mx, my)
    col_border = GOLD if hovered or active else (80, 80, 90)
    col_text   = GOLD if hovered or active else (180, 180, 180)
    pygame.draw.rect(screen, (15, 15, 20), rect)
    pygame.draw.rect(screen, col_border, rect, 1)
    txt = font.render(label, True, col_text)
    screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
    return hovered


def is_clicked(rect, events):
    for e in events:
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if rect.collidepoint(e.pos):
                return True
    return False


# ---------------------------------------------------------------------------
# Username input screen (returns username string)
# ---------------------------------------------------------------------------

def screen_username_input():
    username  = ""
    cursor_on = True
    cursor_timer = pygame.time.get_ticks()

    while True:
        clock.tick(30)
        events = pygame.event.get()

        for e in events:
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN and username.strip():
                    return username.strip()
                elif e.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                elif len(username) < 20 and e.unicode.isprintable():
                    username += e.unicode

        # Cursor blink
        if pygame.time.get_ticks() - cursor_timer > 500:
            cursor_on = not cursor_on
            cursor_timer = pygame.time.get_ticks()

        draw_bg()
        draw_text_center("SNAKE", font_big, GOLD, 60)
        draw_text_center("Enter your username:", font_med, WHITE, 140)

        # Input box
        box = pygame.Rect(70, 170, 260, 32)
        pygame.draw.rect(screen, (15, 15, 20), box)
        pygame.draw.rect(screen, GOLD, box, 1)
        display = username + ("|" if cursor_on else " ")
        t = font_med.render(display, True, WHITE)
        screen.blit(t, (box.x + 6, box.y + 7))

        draw_text_center("Press ENTER to continue", font_sm, (100, 100, 120), 220)

        if not db_available:
            draw_text_center("(DB offline — scores won't be saved)", font_sm, (180, 80, 80), 250)

        pygame.display.update()


# ---------------------------------------------------------------------------
# Main Menu
# ---------------------------------------------------------------------------

def screen_main_menu(username):
    btn_play  = pygame.Rect(130, 170, 140, 30)
    btn_lb    = pygame.Rect(130, 215, 140, 30)
    btn_set   = pygame.Rect(130, 260, 140, 30)
    btn_quit  = pygame.Rect(130, 305, 140, 30)

    while True:
        clock.tick(30)
        events = pygame.event.get()

        for e in events:
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        draw_bg()
        draw_text_center("SNAKE", font_big, GOLD, 60)
        draw_text_center(f"Player: {username}", font_sm, (160, 160, 160), 115)

        draw_button("PLAY",        font_med, btn_play)
        draw_button("LEADERBOARD", font_med, btn_lb)
        draw_button("SETTINGS",    font_med, btn_set)
        draw_button("QUIT",        font_med, btn_quit)

        if is_clicked(btn_play,  events): return SCREEN_GAME
        if is_clicked(btn_lb,    events): return SCREEN_LEADERBOARD
        if is_clicked(btn_set,   events): return SCREEN_SETTINGS
        if is_clicked(btn_quit,  events): pygame.quit(); sys.exit()

        pygame.display.update()


# ---------------------------------------------------------------------------
# Game Over Screen
# ---------------------------------------------------------------------------

def screen_game_over(score, level, personal_best):
    btn_retry = pygame.Rect(100, 260, 100, 30)
    btn_menu  = pygame.Rect(210, 260, 100, 30)

    while True:
        clock.tick(30)
        events = pygame.event.get()

        for e in events:
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        draw_bg()
        draw_text_center("GAME OVER", font_big, RED, 60)
        draw_text_center(f"Score : {score}",        font_med, WHITE,            130)
        draw_text_center(f"Level : {level}",        font_med, WHITE,            155)
        draw_text_center(f"Best  : {personal_best}", font_med, GOLD,            180)

        draw_button("RETRY",     font_med, btn_retry)
        draw_button("MAIN MENU", font_med, btn_menu)

        if is_clicked(btn_retry, events): return SCREEN_GAME
        if is_clicked(btn_menu,  events): return SCREEN_MENU

        pygame.display.update()


# ---------------------------------------------------------------------------
# Leaderboard Screen
# ---------------------------------------------------------------------------

def screen_leaderboard():
    btn_back = pygame.Rect(150, 360, 100, 28)
    rows     = db.get_leaderboard(10) if db_available else []

    while True:
        clock.tick(30)
        events = pygame.event.get()

        for e in events:
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        draw_bg()
        draw_text_center("TOP 10", font_big, GOLD, 18)

        # Header
        header = font_sm.render(
            f"{'#':<3} {'Name':<14} {'Score':>6}  {'Lvl':>3}  {'Date':<10}", True, (150, 150, 160)
        )
        screen.blit(header, (20, 60))
        pygame.draw.line(screen, (60, 60, 70), (20, 76), (SCREEN_WIDTH - 20, 76))

        if rows:
            for i, (rank, uname, sc, lvl, date) in enumerate(rows):
                col = GOLD if rank == 1 else WHITE
                line = font_sm.render(
                    f"{rank:<3} {uname[:13]:<14} {sc:>6}  {lvl:>3}  {date:<10}", True, col
                )
                screen.blit(line, (20, 82 + i * 18))
        else:
            draw_text_center(
                "No scores yet" if db_available else "DB offline",
                font_med, (150, 150, 150), 180
            )

        draw_button("BACK", font_med, btn_back)
        if is_clicked(btn_back, events):
            return

        pygame.display.update()


# ---------------------------------------------------------------------------
# Settings Screen
# ---------------------------------------------------------------------------

def screen_settings():
    global settings

    btn_grid    = pygame.Rect(210, 140, 100, 26)
    btn_sound   = pygame.Rect(210, 178, 100, 26)
    btn_color_r = pygame.Rect(100, 216, 60, 26)
    btn_color_g = pygame.Rect(170, 216, 60, 26)
    btn_color_b = pygame.Rect(240, 216, 60, 26)
    btn_save    = pygame.Rect(120, 330, 160, 30)

    tmp = dict(settings)  # work on a copy

    COLOR_PRESETS = [
        (255, 255, 255), (255, 100, 100), (100, 255, 100),
        (100, 180, 255), (255, 215, 0),   (200, 100, 255),
    ]

    color_idx = 0
    # Try to find current color in presets
    cur_col = tuple(tmp.get("snake_color", [255, 255, 255]))
    for i, p in enumerate(COLOR_PRESETS):
        if p == cur_col:
            color_idx = i
            break

    while True:
        clock.tick(30)
        events = pygame.event.get()

        for e in events:
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        draw_bg()
        draw_text_center("SETTINGS", font_big, GOLD, 30)

        # Grid toggle
        t = font_med.render("Grid Overlay:", True, WHITE)
        screen.blit(t, (20, 145))
        draw_button("ON" if tmp["grid_overlay"] else "OFF", font_med, btn_grid,
                    active=tmp["grid_overlay"])

        # Sound toggle
        t = font_med.render("Sound:", True, WHITE)
        screen.blit(t, (20, 183))
        draw_button("ON" if tmp["sound"] else "OFF", font_med, btn_sound,
                    active=tmp["sound"])

        # Snake color picker
        t = font_med.render("Snake Color:", True, WHITE)
        screen.blit(t, (20, 221))
        # Draw color swatches
        for i, col in enumerate(COLOR_PRESETS):
            bx = 100 + i * 50
            swatch = pygame.Rect(bx, 216, 26, 26)
            pygame.draw.rect(screen, col, swatch)
            if i == color_idx:
                pygame.draw.rect(screen, GOLD, swatch, 2)

        # Preview
        preview_col = COLOR_PRESETS[color_idx]
        t = font_sm.render("Preview:", True, (150, 150, 160))
        screen.blit(t, (20, 260))
        pygame.draw.rect(screen, preview_col, (90, 258, 40, 12))

        draw_button("SAVE & BACK", font_med, btn_save)

        # Interactions
        if is_clicked(btn_grid,  events): tmp["grid_overlay"] = not tmp["grid_overlay"]
        if is_clicked(btn_sound, events): tmp["sound"]        = not tmp["sound"]

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i, col in enumerate(COLOR_PRESETS):
                    bx = 100 + i * 50
                    swatch = pygame.Rect(bx, 216, 26, 26)
                    if swatch.collidepoint(e.pos):
                        color_idx = i

        if is_clicked(btn_save, events):
            tmp["snake_color"] = list(COLOR_PRESETS[color_idx])
            settings = tmp
            sett_mod.save_settings(settings)
            return

        pygame.display.update()


# ---------------------------------------------------------------------------
# Main State Machine
# ---------------------------------------------------------------------------

def main():
    global settings

    username    = screen_username_input()
    player_id   = db.get_or_create_player(username) if db_available else None
    personal_best = db.get_personal_best(player_id) if player_id else 0

    current_screen = SCREEN_MENU
    last_score, last_level = 0, 1

    while True:
        if current_screen == SCREEN_MENU:
            current_screen = screen_main_menu(username)

        elif current_screen == SCREEN_GAME:
            score, level = run_game(screen, clock, fonts, settings, player_id, personal_best)
            last_score, last_level = score, level
            # Save to DB
            if player_id:
                db.save_session(player_id, score, level)
                personal_best = db.get_personal_best(player_id)
            current_screen = SCREEN_GAMEOVER

        elif current_screen == SCREEN_GAMEOVER:
            current_screen = screen_game_over(last_score, last_level, personal_best)

        elif current_screen == SCREEN_LEADERBOARD:
            screen_leaderboard()
            current_screen = SCREEN_MENU

        elif current_screen == SCREEN_SETTINGS:
            screen_settings()
            current_screen = SCREEN_MENU


if __name__ == "__main__":
    main()
