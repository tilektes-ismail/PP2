# ============================================================
#  ui.py  —  TSIS 3
#  Pure-pygame screens (no external UI libraries):
#    draw_main_menu, draw_settings, draw_leaderboard,
#    draw_game_over, draw_hud, draw_road,
#    username_entry
# ============================================================

import pygame
import os

_HERE = os.path.dirname(os.path.abspath(__file__))

# ---- Colours -----------------------------------------------------------------
BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
RED        = (255, 0,   0)
GREEN      = (0,   200, 0)
YELLOW     = (255, 215, 0)
DARK_GRAY  = (30,  30,  30)
GRAY       = (80,  80,  80)
LIGHT_GRAY = (180, 180, 180)
ROAD_GRAY  = (70,  70,  70)
LANE_WHITE = (230, 230, 230)
NITRO_COL  = (0,   220, 255)
SHIELD_COL = (100, 100, 255)
REPAIR_COL = (0,   220, 80)
ORANGE     = (255, 140, 0)

SCREEN_WIDTH  = 400
SCREEN_HEIGHT = 600

# ---- Fonts (lazy-initialised) ------------------------------------------------
_fonts: dict = {}

def _font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont("Verdana", size, bold=bold)
    return _fonts[key]


# ---- Reusable button helper --------------------------------------------------
def _draw_button(surf, rect, text, active=False, color=None):
    bg = color or (NITRO_COL if active else GRAY)
    pygame.draw.rect(surf, bg, rect, border_radius=8)
    pygame.draw.rect(surf, WHITE, rect, 2, border_radius=8)
    txt = _font(18, bold=True).render(text, True, BLACK if active else WHITE)
    surf.blit(txt, txt.get_rect(center=rect.center))


# ==============================================================================
#  Road background
# ==============================================================================

def draw_road(surf, scroll_y: int):
    """Scrolling road with lane markings."""
    surf.fill(ROAD_GRAY)

    # Kerbs (green strips on edges)
    pygame.draw.rect(surf, GREEN, (0, 0, 30, SCREEN_HEIGHT))
    pygame.draw.rect(surf, GREEN, (SCREEN_WIDTH - 30, 0, 30, SCREEN_HEIGHT))

    # Asphalt
    pygame.draw.rect(surf, (60, 60, 60), (30, 0, SCREEN_WIDTH - 60, SCREEN_HEIGHT))

    # Lane markings (dashed white)
    for lx in [140, 260]:
        for y in range(-60, SCREEN_HEIGHT + 60, 60):
            ry = (y + scroll_y) % (SCREEN_HEIGHT + 60) - 60
            pygame.draw.rect(surf, LANE_WHITE, (lx - 2, ry, 4, 35))


# ==============================================================================
#  HUD
# ==============================================================================

def draw_hud(surf, score, coins, distance, speed,
             active_powerup, powerup_timer, fps,
             has_shield, nitro_active, oil_timer=0, nitro_strip_timer=0):
    """Render the in-game HUD overlay."""
    f_sm  = _font(16)
    f_med = _font(18, bold=True)

    # Semi-transparent top bar
    bar = pygame.Surface((SCREEN_WIDTH, 48), pygame.SRCALPHA)
    bar.fill((0, 0, 0, 140))
    surf.blit(bar, (0, 0))

    # Score
    surf.blit(f_sm.render(f"Score: {score}", True, WHITE), (6, 4))
    # Coins
    surf.blit(f_sm.render(f"Coins: {coins}", True, YELLOW), (6, 24))
    # Distance
    surf.blit(f_sm.render(f"Dist: {distance}m", True, LIGHT_GRAY), (150, 4))
    # Speed
    surf.blit(f_sm.render(f"Spd: {speed:.1f}", True, LIGHT_GRAY), (150, 24))

    # Power-up status
    if active_powerup:
        pu_colors = {"nitro": NITRO_COL, "shield": SHIELD_COL, "repair": REPAIR_COL}
        col = pu_colors.get(active_powerup, WHITE)
        label = active_powerup.upper()
        if powerup_timer > 0:
            secs = powerup_timer / fps
            label += f" {secs:.1f}s"
        txt = f_med.render(label, True, col)
        surf.blit(txt, (SCREEN_WIDTH - txt.get_width() - 8, 6))

    # Shield icon
    if has_shield:
        pygame.draw.circle(surf, SHIELD_COL, (SCREEN_WIDTH - 16, 38), 10)
        pygame.draw.circle(surf, WHITE,      (SCREEN_WIDTH - 16, 38), 10, 2)

    # Oil slow warning
    if oil_timer > 0:
        secs = oil_timer / fps
        warn = _font(16, bold=True).render(f"OIL! SLOWED {secs:.1f}s", True, (180, 80, 255))
        surf.blit(warn, warn.get_rect(center=(SCREEN_WIDTH // 2, 56)))

    # Nitro strip boost notification
    if nitro_strip_timer > 0:
        secs = nitro_strip_timer / fps
        boost = _font(16, bold=True).render(f"⚡ BOOST! {secs:.1f}s", True, NITRO_COL)
        surf.blit(boost, boost.get_rect(center=(SCREEN_WIDTH // 2, 56)))


# ==============================================================================
#  Main Menu
# ==============================================================================

def draw_main_menu(surf) -> dict:
    """Draw main menu; returns dict of {action: pygame.Rect}."""
    surf.fill(DARK_GRAY)

    # Title
    title = _font(48, bold=True).render("CAR DODGE", True, YELLOW)
    surf.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 120)))
    sub = _font(18).render("TSIS 3 — Advanced Edition", True, LIGHT_GRAY)
    surf.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 175)))

    buttons = {}
    labels  = [("Play",        "play"),
               ("Leaderboard", "leaderboard"),
               ("Settings",    "settings"),
               ("Quit",        "quit")]
    for i, (label, action) in enumerate(labels):
        rect = pygame.Rect(100, 230 + i * 70, 200, 50)
        _draw_button(surf, rect, label)
        buttons[action] = rect

    return buttons


# ==============================================================================
#  Settings Screen
# ==============================================================================

def draw_settings(surf, settings: dict) -> dict:
    """Draw settings screen; returns dict of {action: pygame.Rect}."""
    surf.fill(DARK_GRAY)
    _font(36, bold=True)

    surf.blit(_font(36, bold=True).render("Settings", True, WHITE),
              _font(36, bold=True).render("Settings", True, WHITE).get_rect(center=(SCREEN_WIDTH // 2, 50)))

    buttons = {}
    y = 110

    # Sound toggle
    sound_label = "Sound: ON" if settings["sound"] else "Sound: OFF"
    r = pygame.Rect(80, y, 240, 44)
    _draw_button(surf, r, sound_label, active=settings["sound"])
    buttons["sound"] = r
    y += 65

    # Car colour
    surf.blit(_font(16).render("Car Color:", True, LIGHT_GRAY), (80, y))
    y += 26
    colors = [("blue", NITRO_COL), ("red", RED), ("yellow", YELLOW)]
    for ci, (col, rgb) in enumerate(colors):
        r = pygame.Rect(60 + ci * 100, y, 85, 40)
        active = settings["car_color"] == col
        _draw_button(surf, r, col.capitalize(), active=active, color=rgb if active else None)
        buttons[f"color_{col}"] = r
    y += 70

    # Difficulty
    surf.blit(_font(16).render("Difficulty:", True, LIGHT_GRAY), (80, y))
    y += 26
    diffs = [("easy", GREEN), ("normal", YELLOW), ("hard", RED)]
    for di, (diff, rgb) in enumerate(diffs):
        r = pygame.Rect(30 + di * 115, y, 100, 40)
        active = settings["difficulty"] == diff
        _draw_button(surf, r, diff.capitalize(), active=active, color=rgb if active else None)
        buttons[f"diff_{diff}"] = r
    y += 70

    # Back
    r = pygame.Rect(100, SCREEN_HEIGHT - 80, 200, 50)
    _draw_button(surf, r, "Back")
    buttons["back"] = r

    return buttons


# ==============================================================================
#  Leaderboard Screen
# ==============================================================================

def draw_leaderboard(surf, entries: list) -> dict:
    """Draw top-10 leaderboard; returns {action: Rect}."""
    surf.fill(DARK_GRAY)
    surf.blit(_font(36, bold=True).render("Leaderboard", True, YELLOW),
              _font(36, bold=True).render("Leaderboard", True, YELLOW).get_rect(
                  center=(SCREEN_WIDTH // 2, 35)))

    header = _font(13, bold=True)
    cols   = _font(13)

    # Column headers
    surf.blit(header.render("#   Name          Score   Dist", True, LIGHT_GRAY), (20, 75))
    pygame.draw.line(surf, GRAY, (20, 93), (SCREEN_WIDTH - 20, 93))

    medals = {0: YELLOW, 1: LIGHT_GRAY, 2: (205, 127, 50)}
    for i, e in enumerate(entries[:10]):
        y    = 100 + i * 44
        col  = medals.get(i, WHITE)
        rank = f"{i+1}."
        name = e.get("name", "???")[:10]
        scr  = str(e.get("score", 0))
        dist = str(e.get("distance", 0)) + "m"
        line = f"{rank:<4}{name:<14}{scr:<8}{dist}"
        surf.blit(cols.render(line, True, col), (20, y))
        if i < 9:
            pygame.draw.line(surf, (50, 50, 50), (20, y + 20), (SCREEN_WIDTH - 20, y + 20))

    if not entries:
        msg = _font(18).render("No entries yet. Play to get on the board!", True, LIGHT_GRAY)
        surf.blit(msg, msg.get_rect(center=(SCREEN_WIDTH // 2, 280)))

    r = pygame.Rect(100, SCREEN_HEIGHT - 70, 200, 50)
    _draw_button(surf, r, "Back")
    return {"back": r}


# ==============================================================================
#  Game Over Screen
# ==============================================================================

def draw_game_over(surf, score, coins, distance) -> dict:
    """Draw game-over screen; returns {action: Rect}."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((180, 0, 0, 200))
    surf.blit(overlay, (0, 0))

    surf.blit(_font(52, bold=True).render("GAME OVER", True, WHITE),
              _font(52, bold=True).render("GAME OVER", True, WHITE).get_rect(
                  center=(SCREEN_WIDTH // 2, 150)))

    f = _font(20)
    stats = [
        (f"Score:    {score}", WHITE),
        (f"Coins:    {coins}", YELLOW),
        (f"Distance: {distance}m", LIGHT_GRAY),
    ]
    for i, (txt, col) in enumerate(stats):
        surf.blit(f.render(txt, True, col),
                  f.render(txt, True, col).get_rect(center=(SCREEN_WIDTH // 2, 240 + i * 36)))

    buttons = {}
    for i, (label, action) in enumerate([("Retry", "retry"), ("Main Menu", "menu")]):
        r = pygame.Rect(50 + i * 180, 390, 160, 50)
        _draw_button(surf, r, label)
        buttons[action] = r

    return buttons


# ==============================================================================
#  Username Entry
# ==============================================================================

def username_entry(surf, clock) -> str:
    """Blocking loop — lets the player type their name, returns it."""
    name = ""
    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and name.strip():
                    done = True
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif len(name) < 12 and event.unicode.isprintable():
                    name += event.unicode

        surf.fill(DARK_GRAY)
        surf.blit(_font(32, bold=True).render("Enter your name", True, WHITE),
                  _font(32, bold=True).render("Enter your name", True, WHITE).get_rect(
                      center=(SCREEN_WIDTH // 2, 200)))

        # Input box
        box = pygame.Rect(60, 270, 280, 48)
        pygame.draw.rect(surf, GRAY, box, border_radius=6)
        pygame.draw.rect(surf, YELLOW, box, 2, border_radius=6)
        surf.blit(_font(24).render(name + "|", True, WHITE), (box.x + 8, box.y + 10))

        surf.blit(_font(15).render("Press Enter to confirm", True, LIGHT_GRAY),
                  _font(15).render("Press Enter to confirm", True, LIGHT_GRAY).get_rect(
                      center=(SCREEN_WIDTH // 2, 345)))

        pygame.display.flip()
        clock.tick(30)

    return name.strip() or "Player"
