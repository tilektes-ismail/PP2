# ============================================================
#  ui.py  —  TSIS 3
#  Pure-pygame screens (no external UI libraries):
#    draw_main_menu, draw_settings, draw_leaderboard,
#    draw_game_over, draw_hud, draw_road,
#    username_entry
# ============================================================
# This file owns everything the player SEES that isn't a moving sprite.
# Every function takes the display Surface as its first argument,
# draws onto it, and returns a dict of button Rects so main.py
# can test mouse clicks without knowing anything about layout.

import pygame
# pygame — needed for drawing rectangles, circles, text, surfaces, etc.

import os
# os — used to build _HERE (the folder path), though this file
# doesn't load any image files directly.

_HERE = os.path.dirname(os.path.abspath(__file__))
# Absolute path to the folder containing ui.py.
# Available if this file ever needs to load local assets (fonts, images).

# ---- Colours -----------------------------------------------------------------
# RGB tuples used throughout every screen in this file.
# Defined once here to avoid scattering magic numbers in drawing code.
BLACK      = (0,   0,   0)    # Pure black
WHITE      = (255, 255, 255)  # Pure white
RED        = (255, 0,   0)    # Bright red
GREEN      = (0,   200, 0)    # Mid green — road kerb strips
YELLOW     = (255, 215, 0)    # Gold yellow — title, coins, active highlights
DARK_GRAY  = (30,  30,  30)   # Near-black — background for all menu screens
GRAY       = (80,  80,  80)   # Medium gray — inactive button backgrounds
LIGHT_GRAY = (180, 180, 180)  # Light gray — secondary HUD text, leaderboard text
ROAD_GRAY  = (70,  70,  70)   # Road surface color
LANE_WHITE = (230, 230, 230)  # Lane divider dashes
NITRO_COL  = (0,   220, 255)  # Cyan — nitro power-up, active button highlight
SHIELD_COL = (100, 100, 255)  # Soft blue — shield power-up indicator
REPAIR_COL = (0,   220, 80)   # Bright green — repair power-up indicator
ORANGE     = (255, 140, 0)    # Orange — available for warnings / barrier coloring

SCREEN_WIDTH  = 400   # Pixel width of the game window (must match racer.py)
SCREEN_HEIGHT = 600   # Pixel height of the game window (must match racer.py)

# ---- Fonts (lazy-initialised) ------------------------------------------------
_fonts: dict = {}
# Module-level cache: maps (size, bold) → pygame.font.Font object.
# Fonts are expensive to create; caching means each unique size+bold combo
# is only instantiated once, then reused on every subsequent call.

def _font(size: int, bold: bool = False) -> pygame.font.Font:
    # Returns a cached Verdana font at the requested size and weight.
    # "Lazy initialisation" means we only create the font the first time it's needed.

    key = (size, bold)
    # The cache key is a tuple of both parameters — (16, False) and (16, True)
    # are different fonts and must be stored separately.

    if key not in _fonts:
        # Font hasn't been created yet — create and cache it now.
        _fonts[key] = pygame.font.SysFont("Verdana", size, bold=bold)
        # SysFont looks for Verdana installed on the OS.
        # If Verdana isn't found, pygame falls back to its default font automatically.

    return _fonts[key]
    # Return the cached Font object (already created or just created above).


# ---- Reusable button helper --------------------------------------------------
def _draw_button(surf, rect, text, active=False, color=None):
    # Draws a single rounded-rectangle button onto `surf`.
    # Used by every screen that has clickable buttons.
    # Arguments:
    #   surf   — the Surface to draw onto
    #   rect   — pygame.Rect defining position and size of the button
    #   text   — label string displayed inside the button
    #   active — if True, button is highlighted (e.g. currently selected option)
    #   color  — optional override for the background color

    bg = color or (NITRO_COL if active else GRAY)
    # Pick the background color:
    #   If a color override was passed in → use it.
    #   Else if active=True → use cyan (NITRO_COL) to highlight selected state.
    #   Else → use medium GRAY for a normal/inactive button.

    pygame.draw.rect(surf, bg, rect, border_radius=8)
    # Draw the filled background rectangle with rounded corners (radius=8px).

    pygame.draw.rect(surf, WHITE, rect, 2, border_radius=8)
    # Draw a 2px white border outline on top of the fill.
    # The border_radius must be repeated here or the outline would have square corners.

    txt = _font(18, bold=True).render(text, True, BLACK if active else WHITE)
    # Render the label text:
    #   Font: bold Verdana size 18.
    #   True = anti-aliased edges (smooth text).
    #   Color: BLACK text on active (cyan) buttons, WHITE text on gray buttons.
    #   .render() returns a new Surface containing the drawn text.

    surf.blit(txt, txt.get_rect(center=rect.center))
    # Position the text Surface so its center aligns with the button's center.
    # txt.get_rect(center=rect.center) creates a Rect the size of the text,
    # positioned so its center matches the button's center — this centers the label.


# ==============================================================================
#  Road background
# ==============================================================================

def draw_road(surf, scroll_y: int):
    """Scrolling road with lane markings."""
    # Draws the complete road background every frame.
    # scroll_y is the current scroll offset — lane dashes shift by this amount
    # to create the illusion of forward motion.

    surf.fill(ROAD_GRAY)
    # Fill the entire display with road gray as the base layer.
    # Every subsequent draw call paints ON TOP of this.

    # Kerbs (green strips on edges)
    pygame.draw.rect(surf, GREEN, (0, 0, 30, SCREEN_HEIGHT))
    # Draw a 30px-wide green strip along the LEFT edge (x=0, full height).
    # Represents the grass/kerb boundary.

    pygame.draw.rect(surf, GREEN, (SCREEN_WIDTH - 30, 0, 30, SCREEN_HEIGHT))
    # Draw a 30px-wide green strip along the RIGHT edge.
    # SCREEN_WIDTH - 30 = 370, so it runs from x=370 to x=400.

    # Asphalt
    pygame.draw.rect(surf, (60, 60, 60), (30, 0, SCREEN_WIDTH - 60, SCREEN_HEIGHT))
    # Draw the dark asphalt strip between the two kerbs.
    # Starts at x=30 (after left kerb), width = 400-60 = 340px.
    # Slightly darker than ROAD_GRAY to visually distinguish road from kerb.

    # Lane markings (dashed white)
    for lx in [140, 260]:
        # Two vertical dashed lines: at x=140 (left lane divider) and x=260 (right).
        # These x-positions are between LANE_CENTERS [80, 200, 320].

        for y in range(-60, SCREEN_HEIGHT + 60, 60):
            # Generate y-positions for each dash, starting 60px above screen top
            # and ending 60px below screen bottom (the extra range ensures no gaps
            # when the scroll offset shifts dashes near the edges).
            # Dashes are spaced 60px apart: one 35px dash + 25px gap.

            ry = (y + scroll_y) % (SCREEN_HEIGHT + 60) - 60
            # Apply the scroll offset to shift every dash downward.
            # % (SCREEN_HEIGHT + 60) wraps around so dashes loop seamlessly.
            # Subtracting 60 brings the range back to [-60, SCREEN_HEIGHT).

            pygame.draw.rect(surf, LANE_WHITE, (lx - 2, ry, 4, 35))
            # Draw a 4×35px white dash centered on lx (lx-2 to lx+2).
            # Width=4 makes it a thin, clean line.


# ==============================================================================
#  HUD
# ==============================================================================

def draw_hud(surf, score, coins, distance, speed,
             active_powerup, powerup_timer, fps,
             has_shield, nitro_active, oil_timer=0, nitro_strip_timer=0):
    """Render the in-game HUD overlay."""
    # Draws the semi-transparent stats bar at the top of the screen
    # and any active status indicators (power-up timers, warnings).
    # Called every frame after all sprites are drawn, so it appears on top.

    f_sm  = _font(16)           # Small font — stats text
    f_med = _font(18, bold=True) # Medium bold — power-up label

    # Semi-transparent top bar
    bar = pygame.Surface((SCREEN_WIDTH, 48), pygame.SRCALPHA)
    # Create a 400×48 surface with per-pixel alpha (SRCALPHA).
    # This allows us to fill it with a color that includes an alpha value.

    bar.fill((0, 0, 0, 140))
    # Fill with black at 140/255 opacity (~55% transparent).
    # The road and sprites below are still partially visible through it.

    surf.blit(bar, (0, 0))
    # Draw the transparent bar at the top-left corner of the display.

    # Score
    surf.blit(f_sm.render(f"Score: {score}", True, WHITE), (6, 4))
    # Render "Score: 1234" in white and place it at (6, 4) — top-left of the HUD bar.

    # Coins
    surf.blit(f_sm.render(f"Coins: {coins}", True, YELLOW), (6, 24))
    # Render coin count in yellow directly below the score.

    # Distance
    surf.blit(f_sm.render(f"Dist: {distance}m", True, LIGHT_GRAY), (150, 4))
    # Distance in light gray, horizontally offset to the center of the bar.

    # Speed
    surf.blit(f_sm.render(f"Spd: {speed:.1f}", True, LIGHT_GRAY), (150, 24))
    # Speed formatted to 1 decimal place (e.g. "Spd: 7.5"), below distance.

    # Power-up status
    if active_powerup:
        # Only draw if a power-up is currently active.

        pu_colors = {"nitro": NITRO_COL, "shield": SHIELD_COL, "repair": REPAIR_COL}
        col = pu_colors.get(active_powerup, WHITE)
        # Look up the color for this power-up type; fall back to WHITE if unknown.

        label = active_powerup.upper()
        # Start with the power-up name in uppercase: "NITRO", "SHIELD", "REPAIR".

        if powerup_timer > 0:
            secs = powerup_timer / fps
            label += f" {secs:.1f}s"
            # Append the remaining duration in seconds, e.g. "NITRO 2.3s".
            # powerup_timer is in frames; dividing by fps converts to seconds.

        txt = f_med.render(label, True, col)
        # Render the label in the power-up's color using the medium bold font.

        surf.blit(txt, (SCREEN_WIDTH - txt.get_width() - 8, 6))
        # Right-align the text: position x = screen width - text width - 8px margin.
        # This keeps it in the top-right corner of the HUD bar.

    # Shield icon
    if has_shield:
        # Draw a small circular shield icon when the shield power-up is active.

        pygame.draw.circle(surf, SHIELD_COL, (SCREEN_WIDTH - 16, 38), 10)
        # Filled blue circle at the bottom-right of the HUD bar.
        # Center: (384, 38), radius: 10px.

        pygame.draw.circle(surf, WHITE, (SCREEN_WIDTH - 16, 38), 10, 2)
        # White 2px outline on top of the filled circle for definition.

    # Oil slow warning
    if oil_timer > 0:
        # Show a warning banner when the player is slowed by an oil spill.

        secs = oil_timer / fps
        # Convert remaining frames to seconds.

        warn = _font(16, bold=True).render(f"OIL! SLOWED {secs:.1f}s", True, (180, 80, 255))
        # Render the warning in purple (matching oil spill color) — bold for urgency.

        surf.blit(warn, warn.get_rect(center=(SCREEN_WIDTH // 2, 56)))
        # Center the warning horizontally, just below the HUD bar (y=56).

    # Nitro strip boost notification
    if nitro_strip_timer > 0:
        # Show a boost notification when the player drove over a nitro strip.
        # Note: this if-block can overlap with the oil warning above since
        # both render at y=56 — in practice they shouldn't both be active simultaneously.

        secs = nitro_strip_timer / fps
        # Convert remaining boost frames to seconds.

        boost = _font(16, bold=True).render(f"⚡ BOOST! {secs:.1f}s", True, NITRO_COL)
        # Render "⚡ BOOST! 1.8s" in cyan with a lightning bolt emoji.

        surf.blit(boost, boost.get_rect(center=(SCREEN_WIDTH // 2, 56)))
        # Center the notification below the HUD bar, same y-position as the oil warning.


# ==============================================================================
#  Main Menu
# ==============================================================================

def draw_main_menu(surf) -> dict:
    """Draw main menu; returns dict of {action: pygame.Rect}."""
    # Draws the main menu screen and returns button Rects so main.py
    # can detect which button was clicked.

    surf.fill(DARK_GRAY)
    # Fill the screen with near-black background.

    # Title
    title = _font(48, bold=True).render("CAR DODGE", True, YELLOW)
    # Render the game title in large bold gold text.

    surf.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 120)))
    # Center the title horizontally at y=120 (upper portion of screen).

    sub = _font(18).render("TSIS 3 — Advanced Edition", True, LIGHT_GRAY)
    # Render a smaller subtitle in light gray.

    surf.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 175)))
    # Center the subtitle below the title at y=175.

    buttons = {}
    # Dict that will map action names → Rect objects and be returned to main.py.

    labels  = [("Play",        "play"),
               ("Leaderboard", "leaderboard"),
               ("Settings",    "settings"),
               ("Quit",        "quit")]
    # List of (display_label, action_key) pairs — one per button, in top-to-bottom order.

    for i, (label, action) in enumerate(labels):
        # i=0: Play, i=1: Leaderboard, i=2: Settings, i=3: Quit

        rect = pygame.Rect(100, 230 + i * 70, 200, 50)
        # Create a 200×50 Rect for each button.
        # x=100 centers a 200px button in a 400px screen.
        # y starts at 230 and increments by 70px per button (50px height + 20px gap).

        _draw_button(surf, rect, label)
        # Draw the button (gray background, white border, white label).

        buttons[action] = rect
        # Store the Rect under the action key so main.py can test: 
        # if buttons["play"].collidepoint(mouse_pos): ...

    return buttons
    # Return {"play": Rect, "leaderboard": Rect, "settings": Rect, "quit": Rect}


# ==============================================================================
#  Settings Screen
# ==============================================================================

def draw_settings(surf, settings: dict) -> dict:
    """Draw settings screen; returns dict of {action: pygame.Rect}."""
    # Draws the settings screen with toggleable options for sound, car color,
    # and difficulty. Returns all button Rects so main.py can handle clicks.

    surf.fill(DARK_GRAY)
    # Dark background for the settings screen.

    _font(36, bold=True)
    # This call creates and caches the font but discards the result.
    # It's a no-op (the result is unused) — likely a leftover line from development.
    # The font IS used two lines below, where _font(36, bold=True) is called again.

    surf.blit(_font(36, bold=True).render("Settings", True, WHITE),
              _font(36, bold=True).render("Settings", True, WHITE).get_rect(center=(SCREEN_WIDTH // 2, 50)))
    # Render the "Settings" title twice — once to get the Surface, once to get its centered Rect.
    # This is slightly inefficient (renders the text twice); a single render + separate get_rect call
    # would be cleaner, but it works correctly.
    # Result: "Settings" centered horizontally at y=50.

    buttons = {}
    # Will collect all button Rects to return.

    y = 110
    # Starting y-position for the first control; incremented as we add rows.

    # Sound toggle
    sound_label = "Sound: ON" if settings["sound"] else "Sound: OFF"
    # Build the button label dynamically based on the current sound setting.

    r = pygame.Rect(80, y, 240, 44)
    # Sound toggle button: 240×44px, centered-ish at x=80.

    _draw_button(surf, r, sound_label, active=settings["sound"])
    # Draw the button. active=True (sound on) → cyan background, active=False → gray.

    buttons["sound"] = r
    # Store so main.py can detect: if buttons["sound"].collidepoint(pos): toggle sound.

    y += 65
    # Move down 65px for the next section (44px button + 21px gap).

    # Car colour
    surf.blit(_font(16).render("Car Color:", True, LIGHT_GRAY), (80, y))
    # Draw a "Car Color:" label in light gray above the color buttons.

    y += 26
    # Move down 26px (past the label) to where the color buttons start.

    colors = [("blue", NITRO_COL), ("red", RED), ("yellow", YELLOW)]
    # Three color options: each is (settings_value, highlight_color_when_active).

    for ci, (col, rgb) in enumerate(colors):
        # ci=0: blue, ci=1: red, ci=2: yellow

        r = pygame.Rect(60 + ci * 100, y, 85, 40)
        # Position buttons side by side, each 85px wide, spaced 100px apart.
        # Starts at x=60, then x=160, then x=260.

        active = settings["car_color"] == col
        # True if this color is the currently selected one.

        _draw_button(surf, r, col.capitalize(), active=active, color=rgb if active else None)
        # Draw the button. If active: use the color's own RGB as background (e.g. cyan for blue).
        # If inactive: color=None → _draw_button uses GRAY.

        buttons[f"color_{col}"] = r
        # Store as "color_blue", "color_red", "color_yellow" for main.py click detection.

    y += 70
    # Move down 70px for the difficulty section.

    # Difficulty
    surf.blit(_font(16).render("Difficulty:", True, LIGHT_GRAY), (80, y))
    # Draw "Difficulty:" label above the difficulty buttons.

    y += 26
    # Move down past the label.

    diffs = [("easy", GREEN), ("normal", YELLOW), ("hard", RED)]
    # Three difficulty options with color-coded highlights (green/yellow/red).

    for di, (diff, rgb) in enumerate(diffs):
        # di=0: easy, di=1: normal, di=2: hard

        r = pygame.Rect(30 + di * 115, y, 100, 40)
        # Position buttons side by side, 100px wide, spaced 115px apart.
        # Starts at x=30, then x=145, then x=260.

        active = settings["difficulty"] == diff
        # True if this is the currently selected difficulty.

        _draw_button(surf, r, diff.capitalize(), active=active, color=rgb if active else None)
        # Draw with color highlight if selected; gray if not.

        buttons[f"diff_{diff}"] = r
        # Store as "diff_easy", "diff_normal", "diff_hard".

    y += 70
    # Move down for the back button (this y value isn't actually used —
    # the back button is pinned to a fixed position near the screen bottom).

    # Back
    r = pygame.Rect(100, SCREEN_HEIGHT - 80, 200, 50)
    # Place the Back button 80px from the bottom of the screen, centered horizontally.

    _draw_button(surf, r, "Back")
    # Draw as a standard inactive (gray) button.

    buttons["back"] = r

    return buttons
    # Return all button Rects for main.py to use in click detection.


# ==============================================================================
#  Leaderboard Screen
# ==============================================================================

def draw_leaderboard(surf, entries: list) -> dict:
    """Draw top-10 leaderboard; returns {action: Rect}."""
    # Renders the leaderboard table showing up to 10 past run results.
    # Top 3 entries are highlighted in gold, silver, and bronze.

    surf.fill(DARK_GRAY)
    # Dark background.

    surf.blit(_font(36, bold=True).render("Leaderboard", True, YELLOW),
              _font(36, bold=True).render("Leaderboard", True, YELLOW).get_rect(
                  center=(SCREEN_WIDTH // 2, 35)))
    # Draw the "Leaderboard" title in gold, centered at y=35.
    # Again renders twice (Surface for blit, Rect for centering) — same pattern as Settings.

    header = _font(13, bold=True)
    # Small bold font for the column header row.

    cols   = _font(13)
    # Same size, non-bold, for data rows.

    # Column headers
    surf.blit(header.render("#   Name          Score   Dist", True, LIGHT_GRAY), (20, 75))
    # Draw a text header row showing column names at x=20, y=75.
    # Uses fixed-width spacing to align with the data rows below (via Python format strings).

    pygame.draw.line(surf, GRAY, (20, 93), (SCREEN_WIDTH - 20, 93))
    # Draw a horizontal separator line at y=93, spanning from x=20 to x=380.

    medals = {0: YELLOW, 1: LIGHT_GRAY, 2: (205, 127, 50)}
    # Maps rank index → color:
    #   0 (1st place) → gold
    #   1 (2nd place) → silver
    #   2 (3rd place) → bronze (205, 127, 50)
    # Any rank beyond 2 falls back to WHITE below.

    for i, e in enumerate(entries[:10]):
        # Iterate over up to the top 10 entries (slice prevents IndexError if fewer exist).
        # i = 0-based index; e = the entry dict {"name": ..., "score": ..., ...}

        y    = 100 + i * 44
        # Each row is 44px tall, starting at y=100.
        # Row 0: y=100, Row 1: y=144, Row 2: y=188, ...

        col  = medals.get(i, WHITE)
        # Get the medal color for this rank, defaulting to WHITE for 4th place and beyond.

        rank = f"{i+1}."
        # "1.", "2.", "3.", etc.

        name = e.get("name", "???")[:10]
        # Get the player name, defaulting to "???" if missing.
        # [:10] truncates to 10 characters max so it doesn't overflow the column.

        scr  = str(e.get("score", 0))
        # Score as a string, defaulting to "0" if missing.

        dist = str(e.get("distance", 0)) + "m"
        # Distance as a string with "m" suffix, e.g. "3420m".

        line = f"{rank:<4}{name:<14}{scr:<8}{dist}"
        # Build a fixed-width formatted string using Python f-string alignment:
        #   rank:<4  — left-aligned in 4 chars: "1.  "
        #   name:<14 — left-aligned in 14 chars: "Alice         "
        #   scr:<8   — left-aligned in 8 chars:  "420     "
        #   dist     — no padding (last column)
        # This aligns all rows into consistent columns when rendered with a monospaced-ish font.

        surf.blit(cols.render(line, True, col), (20, y))
        # Render the row text in the medal color and draw it at (20, y).

        if i < 9:
            pygame.draw.line(surf, (50, 50, 50), (20, y + 20), (SCREEN_WIDTH - 20, y + 20))
            # Draw a subtle dark separator line below each row except the last.
            # (50, 50, 50) is slightly lighter than the background, creating a faint grid.

    if not entries:
        # No entries in the leaderboard yet (first time playing).
        msg = _font(18).render("No entries yet. Play to get on the board!", True, LIGHT_GRAY)
        surf.blit(msg, msg.get_rect(center=(SCREEN_WIDTH // 2, 280)))
        # Display a friendly prompt centered on the screen.

    r = pygame.Rect(100, SCREEN_HEIGHT - 70, 200, 50)
    # Back button: 200×50, centered horizontally, 70px from the bottom.

    _draw_button(surf, r, "Back")
    return {"back": r}
    # Only one button on this screen, returned directly as a one-entry dict.


# ==============================================================================
#  Game Over Screen
# ==============================================================================

def draw_game_over(surf, score, coins, distance) -> dict:
    """Draw game-over screen; returns {action: Rect}."""
    # Overlays a semi-transparent red screen on top of the last gameplay frame,
    # showing final stats and offering Retry / Main Menu buttons.

    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    # Full-screen surface with per-pixel alpha so we can use a transparent fill.

    overlay.fill((180, 0, 0, 200))
    # Fill with dark red at 200/255 opacity (~78% opaque).
    # The gameplay frame drawn underneath is still faintly visible, giving a "crash effect".

    surf.blit(overlay, (0, 0))
    # Draw the red overlay covering the entire display.

    surf.blit(_font(52, bold=True).render("GAME OVER", True, WHITE),
              _font(52, bold=True).render("GAME OVER", True, WHITE).get_rect(
                  center=(SCREEN_WIDTH // 2, 150)))
    # Draw "GAME OVER" in large bold white text, centered at y=150.
    # Again rendered twice (Surface + Rect) — same pattern as other screens.

    f = _font(20)
    # Medium font for stats text.

    stats = [
        (f"Score:    {score}", WHITE),
        (f"Coins:    {coins}", YELLOW),
        (f"Distance: {distance}m", LIGHT_GRAY),
    ]
    # List of (text_string, color) tuples — one per stat line.
    # Leading spaces in the strings pad labels to visually align the values.

    for i, (txt, col) in enumerate(stats):
        # i=0: Score, i=1: Coins, i=2: Distance

        surf.blit(f.render(txt, True, col),
                  f.render(txt, True, col).get_rect(center=(SCREEN_WIDTH // 2, 240 + i * 36)))
        # Render each stat line centered horizontally.
        # y starts at 240 and increments by 36px per line.
        # Again renders twice — same pattern. An alternative would be:
        #   rendered = f.render(txt, True, col)
        #   surf.blit(rendered, rendered.get_rect(center=(...)))

    buttons = {}
    for i, (label, action) in enumerate([("Retry", "retry"), ("Main Menu", "menu")]):
        # i=0: Retry button, i=1: Main Menu button

        r = pygame.Rect(50 + i * 180, 390, 160, 50)
        # Two 160×50 buttons side by side.
        # i=0: x=50 (left side), i=1: x=230 (right side).
        # Gap between buttons: 230 - (50+160) = 20px.

        _draw_button(surf, r, label)
        # Draw each button as a standard gray button.

        buttons[action] = r
        # Store: {"retry": Rect, "menu": Rect}

    return buttons


# ==============================================================================
#  Username Entry
# ==============================================================================

def username_entry(surf, clock) -> str:
    """Blocking loop — lets the player type their name, returns it."""
    # This function is SYNCHRONOUS (blocking) — it runs its own inner loop
    # and doesn't return until the player presses Enter.
    # main.py calls this before starting a new game and uses the returned name
    # for the leaderboard entry.

    name = ""
    # The string being typed; starts empty and grows as the player types.

    done = False
    # Loop-exit flag; set to True when the player confirms their name.

    while not done:
        # Inner event loop — runs independently of the main game loop.

        for event in pygame.event.get():
            # Drain all queued events each frame of the name-entry screen.

            if event.type == pygame.QUIT:
                # User closed the window while typing — exit immediately.
                pygame.quit()
                raise SystemExit
                # raise SystemExit is cleaner than sys.exit() inside a library function
                # because it doesn't require importing sys here.

            if event.type == pygame.KEYDOWN:
                # A key was pressed (fires once per keypress, not held).

                if event.key == pygame.K_RETURN and name.strip():
                    # Enter key pressed AND the name isn't all whitespace.
                    # name.strip() is truthy if there's at least one non-space character.
                    done = True
                    # Exit the loop on the next iteration.

                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                    # Delete the last character. name[:-1] returns everything except the last char.
                    # If name is already empty, name[:-1] = "" (no error).

                elif len(name) < 12 and event.unicode.isprintable():
                    # Only accept the character if:
                    #   len(name) < 12 — enforces a 12-character max length.
                    #   event.unicode.isprintable() — rejects control characters (arrows, F-keys, etc.)
                    #     and only accepts visible characters (letters, digits, spaces, symbols).
                    name += event.unicode
                    # Append the typed character to the name string.

        # ---- Draw the name-entry screen ----
        surf.fill(DARK_GRAY)
        # Clear the screen each frame (prevents old characters "ghosting").

        surf.blit(_font(32, bold=True).render("Enter your name", True, WHITE),
                  _font(32, bold=True).render("Enter your name", True, WHITE).get_rect(
                      center=(SCREEN_WIDTH // 2, 200)))
        # Draw the prompt text centered at y=200.

        # Input box
        box = pygame.Rect(60, 270, 280, 48)
        # The text input field: 280px wide, 48px tall, positioned at (60, 270).

        pygame.draw.rect(surf, GRAY, box, border_radius=6)
        # Gray filled background for the input field.

        pygame.draw.rect(surf, YELLOW, box, 2, border_radius=6)
        # Yellow 2px border — visually indicates this is the active input area.

        surf.blit(_font(24).render(name + "|", True, WHITE), (box.x + 8, box.y + 10))
        # Render the current name string with a "|" cursor appended.
        # Drawing the cursor as a literal character is simpler than a blinking rect.
        # Position: 8px inside the left edge, 10px below the top of the box.

        surf.blit(_font(15).render("Press Enter to confirm", True, LIGHT_GRAY),
                  _font(15).render("Press Enter to confirm", True, LIGHT_GRAY).get_rect(
                      center=(SCREEN_WIDTH // 2, 345)))
        # Draw small helper text below the input box at y=345.

        pygame.display.flip()
        # Push the drawn frame to the screen.
        # (We must call this manually here because we're outside the main game loop.)

        clock.tick(30)
        # Cap this inner loop at 30 FPS — name entry doesn't need 60 FPS.
        # Also prevents the CPU from running at 100% while waiting for keystrokes.

    return name.strip() or "Player"
    # Strip leading/trailing whitespace from the final name.
    # If the result is an empty string (shouldn't happen due to the check above, but safe),
    # fall back to "Player" as the default username.