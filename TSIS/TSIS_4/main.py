"""
main.py — Entry point. Manages all screens and the game loop.
Screens: Main Menu → Game → Game Over → Leaderboard / Settings.

This file is the "glue" of the whole application: it initializes pygame,
defines every UI screen as its own function, and drives the state machine
that decides which screen to show at any moment.
"""

# pygame: the game/graphics library — must be initialized before any of its features are used
import pygame
# sys: used to call sys.exit() when the player closes the window
import sys

# Import shared constants from config.py
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,              # pixel dimensions of the game window
    BLACK, WHITE, GOLD, RED, GRAY, DARK_GRAY, # named color tuples
    # Screen-state constants — integer IDs that identify which screen is currently active.
    SCREEN_MENU, SCREEN_GAME, SCREEN_GAMEOVER, SCREEN_LEADERBOARD, SCREEN_SETTINGS,
)
# db: module for saving/loading scores and player records from the database
import db
# sett_mod: module for reading and writing user settings (colors, toggles) to disk
import settings as sett_mod
# run_game: the function in game.py that runs one full play session and returns (score, level)
from game import run_game

# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

# Initialize all pygame subsystems (display, fonts, events, etc.)
pygame.init()

# Create the main window surface with the configured pixel dimensions.
# Everything is drawn onto this surface each frame.
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Set the text shown in the OS window title bar.
pygame.display.set_caption("Snake — TSIS 4")

# Create a Clock object used to cap how fast the main loops run (FPS limiter).
clock  = pygame.time.Clock()

# ---- Font setup ----
# Load three sizes of the monospaced "Consolas" system font.
# Monospaced fonts keep columns aligned, which matters for leaderboard tables.
font_sm  = pygame.font.SysFont("Consolas", 13)             # small: HUD labels, hints
font_med = pygame.font.SysFont("Consolas", 18)             # medium: buttons, body text
font_big = pygame.font.SysFont("Consolas", 32, bold=True)  # large bold: screen titles

# Bundle all fonts into a dict so run_game() and other functions can receive them in one argument.
fonts    = {"small": font_sm, "medium": font_med, "big": font_big}

# Attempt to connect to / create the SQLite database.
# Returns True if successful, False if the DB is unavailable.
# The rest of the code checks db_available before any DB calls to fail gracefully.
db_available = db.init_db()

# Load the saved user settings (snake color, grid toggle, sound toggle) from disk.
# Returns a dict with sensible defaults if no settings file exists yet.
settings = sett_mod.load_settings()

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def draw_bg():
    # Fill the entire screen with a very dark near-black background color.
    screen.fill((8, 8, 12))

    # Draw faint horizontal lines every 4 pixels to create a subtle CRT scanline effect.
    # The line color (12, 12, 18) is only slightly lighter than the background.
    for y in range(0, SCREEN_HEIGHT, 4):
        pygame.draw.line(screen, (12, 12, 18), (0, y), (SCREEN_WIDTH, y))


def draw_text_center(text, font, color, y):
    # Render the text string into a pygame Surface.
    surf = font.render(text, True, color)

    # Blit (copy) it onto the screen horizontally centered.
    # SCREEN_WIDTH // 2 - surf.get_width() // 2 computes the X offset so the text is centered.
    # `y` is passed in directly as the vertical position.
    screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, y))


def draw_button(label, font, rect, active=False):
    """Draw a retro button. Returns True if mouse is hovering."""

    # Get the current mouse cursor position in pixels.
    mx, my = pygame.mouse.get_pos()

    # Check if the cursor is inside the button's rectangle.
    hovered = rect.collidepoint(mx, my)

    # Choose border and text colors: gold when hovered or toggled active, dim grey otherwise.
    col_border = GOLD if hovered or active else (80, 80, 90)
    col_text   = GOLD if hovered or active else (180, 180, 180)

    # Draw a near-black filled rectangle as the button background.
    pygame.draw.rect(screen, (15, 15, 20), rect)

    # Draw a 1-pixel border around the button in the chosen border color.
    pygame.draw.rect(screen, col_border, rect, 1)

    # Render the label text surface.
    txt = font.render(label, True, col_text)

    # Blit the label centered inside the button rectangle.
    # rect.centerx / rect.centery give the button's center pixel coordinates.
    screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

    # Return whether the mouse is currently over this button (used for cursor changes or effects).
    return hovered


def is_clicked(rect, events):
    # Scan the list of events that happened this frame.
    for e in events:
        # MOUSEBUTTONDOWN fires when any mouse button is pressed.
        # e.button == 1 filters to left-click only.
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            # collidepoint checks if the click coordinates fall inside the button rectangle.
            if rect.collidepoint(e.pos):
                return True   # this button was clicked this frame
    return False              # no click on this button this frame


# ---------------------------------------------------------------------------
# Username input screen (returns username string)
# ---------------------------------------------------------------------------

def screen_username_input():
    # String that accumulates the characters the player types.
    username  = ""

    # Controls whether the blinking text cursor "|" is visible this half-second.
    cursor_on = True

    # Records the last time the cursor blink state was toggled (in ms).
    cursor_timer = pygame.time.get_ticks()

    while True:
        # Cap the loop at 30 FPS — no need for faster updates on a static input screen.
        clock.tick(30)

        # Collect all pygame events that arrived since the last frame.
        events = pygame.event.get()

        for e in events:
            # Window close button → quit everything immediately.
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if e.type == pygame.KEYDOWN:
                # ENTER/RETURN confirms the name — only if at least one non-space character exists.
                if e.key == pygame.K_RETURN and username.strip():
                    return username.strip()   # return the trimmed username to the caller

                # BACKSPACE removes the last character typed.
                elif e.key == pygame.K_BACKSPACE:
                    username = username[:-1]  # slice off the final character

                # Any other printable character (letters, digits, symbols) is appended,
                # enforcing a 20-character maximum length.
                elif len(username) < 20 and e.unicode.isprintable():
                    username += e.unicode

        # ---- Cursor blink logic ----
        # Every 500 ms, toggle cursor_on between True and False.
        if pygame.time.get_ticks() - cursor_timer > 500:
            cursor_on    = not cursor_on            # flip the visible state
            cursor_timer = pygame.time.get_ticks()  # reset the blink timer

        # ---- Drawing ----
        draw_bg()                                                  # dark scanline background
        draw_text_center("SNAKE", font_big, GOLD, 60)             # game title
        draw_text_center("Enter your username:", font_med, WHITE, 140)  # prompt text

        # ---- Text input box ----
        box = pygame.Rect(70, 170, 260, 32)                        # input field rectangle
        pygame.draw.rect(screen, (15, 15, 20), box)                # dark fill
        pygame.draw.rect(screen, GOLD, box, 1)                     # gold 1-px border

        # Append the blinking cursor character ("|") or a space to the typed text.
        display = username + ("|" if cursor_on else " ")
        t = font_med.render(display, True, WHITE)
        screen.blit(t, (box.x + 6, box.y + 7))                    # 6/7 px padding inside the box

        draw_text_center("Press ENTER to continue", font_sm, (100, 100, 120), 220)

        # Warn the player if the database is unavailable — their score won't be saved.
        if not db_available:
            draw_text_center("(DB offline — scores won't be saved)", font_sm, (180, 80, 80), 250)

        pygame.display.update()   # push the frame to the screen


# ---------------------------------------------------------------------------
# Main Menu
# ---------------------------------------------------------------------------

def screen_main_menu(username):
    # Define the four menu button rectangles (x, y, width, height).
    btn_play  = pygame.Rect(130, 170, 140, 30)
    btn_lb    = pygame.Rect(130, 215, 140, 30)
    btn_set   = pygame.Rect(130, 260, 140, 30)
    btn_quit  = pygame.Rect(130, 305, 140, 30)

    while True:
        clock.tick(30)                         # cap at 30 FPS
        events = pygame.event.get()            # collect events this frame

        for e in events:
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()       # window closed → exit

        draw_bg()
        draw_text_center("SNAKE", font_big, GOLD, 60)                 # title
        draw_text_center(f"Player: {username}", font_sm, (160, 160, 160), 115)  # current player name

        # Draw all four buttons. draw_button() handles hover highlighting automatically.
        draw_button("PLAY",        font_med, btn_play)
        draw_button("LEADERBOARD", font_med, btn_lb)
        draw_button("SETTINGS",    font_med, btn_set)
        draw_button("QUIT",        font_med, btn_quit)

        # Check for left-clicks on each button and return the corresponding screen constant.
        # The state machine in main() will use the returned value to switch screens.
        if is_clicked(btn_play,  events): return SCREEN_GAME         # start a new game
        if is_clicked(btn_lb,    events): return SCREEN_LEADERBOARD  # open leaderboard
        if is_clicked(btn_set,   events): return SCREEN_SETTINGS     # open settings
        if is_clicked(btn_quit,  events): pygame.quit(); sys.exit()  # quit the application

        pygame.display.update()


# ---------------------------------------------------------------------------
# Game Over Screen
# ---------------------------------------------------------------------------

def screen_game_over(score, level, personal_best):
    # Two side-by-side buttons in the lower portion of the screen.
    btn_retry = pygame.Rect(100, 260, 100, 30)
    btn_menu  = pygame.Rect(210, 260, 100, 30)

    while True:
        clock.tick(30)
        events = pygame.event.get()

        for e in events:
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        draw_bg()
        draw_text_center("GAME OVER", font_big, RED, 60)                       # large red title

        # Show the session stats — score, level reached, and all-time personal best.
        draw_text_center(f"Score : {score}",         font_med, WHITE, 130)
        draw_text_center(f"Level : {level}",         font_med, WHITE, 155)
        draw_text_center(f"Best  : {personal_best}", font_med, GOLD,  180)     # PB in gold to stand out

        draw_button("RETRY",     font_med, btn_retry)   # play again immediately
        draw_button("MAIN MENU", font_med, btn_menu)    # go back to the main menu

        # Return the screen constant the state machine should switch to next.
        if is_clicked(btn_retry, events): return SCREEN_GAME   # replay
        if is_clicked(btn_menu,  events): return SCREEN_MENU   # back to menu

        pygame.display.update()


# ---------------------------------------------------------------------------
# Leaderboard Screen
# ---------------------------------------------------------------------------

def screen_leaderboard():
    btn_back = pygame.Rect(150, 360, 100, 28)

    # Fetch the top 10 rows from the DB, or use an empty list if the DB is offline.
    # Each row is a tuple: (rank, username, score, level, date_string)
    rows     = db.get_leaderboard(10) if db_available else []

    while True:
        clock.tick(30)
        events = pygame.event.get()

        for e in events:
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        draw_bg()
        draw_text_center("TOP 10", font_big, GOLD, 18)   # leaderboard title

        # ---- Column header row ----
        # f-string with format specifiers aligns columns:
        # :<3 = left-align in 3 chars, :<14 = left-align in 14, :>6 = right-align in 6, etc.
        header = font_sm.render(
            f"{'#':<3} {'Name':<14} {'Score':>6}  {'Lvl':>3}  {'Date':<10}", True, (150, 150, 160)
        )
        screen.blit(header, (20, 60))   # blit 20px from left, 60px from top

        # Draw a horizontal separator line under the header.
        pygame.draw.line(screen, (60, 60, 70), (20, 76), (SCREEN_WIDTH - 20, 76))

        if rows:
            # Iterate over each leaderboard row with its index for vertical positioning.
            for i, (rank, uname, sc, lvl, date) in enumerate(rows):
                # Highlight rank #1 in gold; all others in white.
                col  = GOLD if rank == 1 else WHITE

                # Truncate usernames longer than 13 chars so the table stays aligned.
                line = font_sm.render(
                    f"{rank:<3} {uname[:13]:<14} {sc:>6}  {lvl:>3}  {date:<10}", True, col
                )
                # Each row is 18 pixels tall; starts at y=82 (just below the separator).
                screen.blit(line, (20, 82 + i * 18))
        else:
            # If there are no rows, show a placeholder message.
            draw_text_center(
                "No scores yet" if db_available else "DB offline",
                font_med, (150, 150, 150), 180
            )

        draw_button("BACK", font_med, btn_back)

        # BACK button just returns (no return value needed — the state machine
        # always goes to SCREEN_MENU after this function returns).
        if is_clicked(btn_back, events):
            return

        pygame.display.update()


# ---------------------------------------------------------------------------
# Settings Screen
# ---------------------------------------------------------------------------

def screen_settings():
    # `global settings` lets this function overwrite the module-level `settings` variable
    # when the player saves, so the new settings are immediately used by the next game.
    global settings

    # Button rectangles for the toggles and save action.
    btn_grid    = pygame.Rect(210, 140, 100, 26)
    btn_sound   = pygame.Rect(210, 178, 100, 26)
    btn_color_r = pygame.Rect(100, 216, 60, 26)   # defined but not currently used — reserved for RGB sliders
    btn_color_g = pygame.Rect(170, 216, 60, 26)
    btn_color_b = pygame.Rect(240, 216, 60, 26)
    btn_save    = pygame.Rect(120, 330, 160, 30)

    # Work on a shallow copy of the settings dict so changes can be discarded
    # if the player navigates away without saving.
    tmp = dict(settings)

    # Six preset snake colors as (R, G, B) tuples.
    COLOR_PRESETS = [
        (255, 255, 255), (255, 100, 100), (100, 255, 100),
        (100, 180, 255), (255, 215, 0),   (200, 100, 255),
    ]

    # Default to the first preset (white).
    color_idx = 0

    # Try to find the player's currently saved color in the presets list.
    cur_col = tuple(tmp.get("snake_color", [255, 255, 255]))
    for i, p in enumerate(COLOR_PRESETS):
        if p == cur_col:
            color_idx = i   # match found — start with this preset selected
            break

    while True:
        clock.tick(30)
        events = pygame.event.get()

        for e in events:
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        draw_bg()
        draw_text_center("SETTINGS", font_big, GOLD, 30)

        # ---- Grid overlay toggle ----
        t = font_med.render("Grid Overlay:", True, WHITE)
        screen.blit(t, (20, 145))   # label on the left
        # Button shows "ON"/"OFF" and is highlighted (active=True) when the feature is enabled.
        draw_button("ON" if tmp["grid_overlay"] else "OFF", font_med, btn_grid,
                    active=tmp["grid_overlay"])

        # ---- Sound toggle ----
        t = font_med.render("Sound:", True, WHITE)
        screen.blit(t, (20, 183))
        draw_button("ON" if tmp["sound"] else "OFF", font_med, btn_sound,
                    active=tmp["sound"])

        # ---- Snake color picker ----
        t = font_med.render("Snake Color:", True, WHITE)
        screen.blit(t, (20, 221))

        # Draw each color swatch as a 26×26 filled rectangle, spaced 50 px apart.
        for i, col in enumerate(COLOR_PRESETS):
            bx     = 100 + i * 50              # X position of this swatch
            swatch = pygame.Rect(bx, 216, 26, 26)
            pygame.draw.rect(screen, col, swatch)   # fill with the preset color

            # Draw a gold 2-px border around the currently selected swatch.
            if i == color_idx:
                pygame.draw.rect(screen, GOLD, swatch, 2)

        # ---- Color preview strip ----
        preview_col = COLOR_PRESETS[color_idx]   # the currently selected color
        t = font_sm.render("Preview:", True, (150, 150, 160))
        screen.blit(t, (20, 260))
        # Draw a small 40×12 rectangle filled with the selected color as a live preview.
        pygame.draw.rect(screen, preview_col, (90, 258, 40, 12))

        draw_button("SAVE & BACK", font_med, btn_save)

        # ---- Interaction handling ----

        # Clicking the grid button flips the boolean value in the working copy.
        if is_clicked(btn_grid,  events): tmp["grid_overlay"] = not tmp["grid_overlay"]

        # Clicking the sound button flips its boolean.
        if is_clicked(btn_sound, events): tmp["sound"]        = not tmp["sound"]

        # Check if any color swatch was clicked this frame.
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i, col in enumerate(COLOR_PRESETS):
                    bx     = 100 + i * 50
                    swatch = pygame.Rect(bx, 216, 26, 26)
                    if swatch.collidepoint(e.pos):
                        color_idx = i   # select the clicked swatch

        # SAVE & BACK: write selected color back into the working copy,
        # overwrite the global settings with the working copy, persist to disk, and return.
        if is_clicked(btn_save, events):
            tmp["snake_color"] = list(COLOR_PRESETS[color_idx])  # store as list (JSON-serializable)
            settings = tmp                                         # replace global settings reference
            sett_mod.save_settings(settings)                      # write to disk
            return                                                 # go back to main menu

        pygame.display.update()


# ---------------------------------------------------------------------------
# Main State Machine
# ---------------------------------------------------------------------------

def main():
    # `global settings` allows the state machine to see changes made inside screen_settings().
    global settings

    # Show the username input screen first; blocks until a name is entered.
    username    = screen_username_input()

    # Look up (or create) a database row for this player; returns a numeric player_id.
    # If the DB is unavailable, player_id stays None and all DB calls are skipped.
    player_id   = db.get_or_create_player(username) if db_available else None

    # Load the player's all-time best score for the HUD and game-over screen.
    personal_best = db.get_personal_best(player_id) if player_id else 0

    # Start at the main menu.
    current_screen = SCREEN_MENU

    # Store the most recent game results so the game-over screen can display them.
    last_score, last_level = 0, 1

    # ---- State machine loop ----
    # Each iteration checks which screen is active and either shows it or transitions.
    while True:
        if current_screen == SCREEN_MENU:
            # screen_main_menu() returns the next screen constant when a button is clicked.
            current_screen = screen_main_menu(username)

        elif current_screen == SCREEN_GAME:
            # Run a full play session; blocks until the player dies or presses ESC.
            score, level = run_game(screen, clock, fonts, settings, player_id, personal_best)

            # Store results so the game-over screen can display them.
            last_score, last_level = score, level

            # If DB is available, persist this session and refresh the personal best.
            if player_id:
                db.save_session(player_id, score, level)
                personal_best = db.get_personal_best(player_id)   # refresh in case a new PB was set

            # Always go to game-over after a game ends.
            current_screen = SCREEN_GAMEOVER

        elif current_screen == SCREEN_GAMEOVER:
            # screen_game_over() returns SCREEN_GAME (retry) or SCREEN_MENU.
            current_screen = screen_game_over(last_score, last_level, personal_best)

        elif current_screen == SCREEN_LEADERBOARD:
            # Leaderboard screen doesn't return a value — always go back to menu after.
            screen_leaderboard()
            current_screen = SCREEN_MENU

        elif current_screen == SCREEN_SETTINGS:
            # Settings screen doesn't return a value — always go back to menu after.
            screen_settings()
            current_screen = SCREEN_MENU


# Standard Python entry-point guard:
# This block only runs when the file is executed directly (python main.py),
# NOT when it is imported as a module by another file.
if __name__ == "__main__":
    main()