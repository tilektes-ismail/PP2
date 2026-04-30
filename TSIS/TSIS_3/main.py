# ============================================================
#  main.py  —  TSIS 3 Car Dodge (Entry Point)
#  Run:  python main.py
#
#  Features added over Practice 10-11:
#    • Main Menu, Settings, Leaderboard, Game Over screens
#    • Lane hazards: oil spills, speed bumps, barriers
#    • Nitro strip road events
#    • Power-ups: Nitro, Shield, Repair
#    • Only one active power-up at a time
#    • Difficulty scaling (enemy count + obstacle rate)
#    • Distance meter + combined score
#    • Persistent leaderboard (leaderboard.json)
#    • Username entry
#    • Settings persistence (settings.json)
# ============================================================
# This block is just a big docstring/comment describing the whole file.
# It lists every major feature so any reader knows what this file does
# before reading a single line of actual code.

import pygame, sys, os, time, random
# pygame  — the game library: handles window, drawing, input, sound, sprites
# sys     — lets us exit the program cleanly with sys.exit()
# os      — used to build file paths that work on every operating system
# time    — used for time.sleep() (brief pause on crash)
# random  — used to generate random spawn timers for obstacles and power-ups
from pygame.locals import QUIT
# QUIT is the constant for the "user closed the window" event.
# Importing it directly saves typing pygame.locals.QUIT everywhere.

_HERE = os.path.dirname(os.path.abspath(__file__))
# __file__ is the path to THIS script file.
# os.path.abspath() converts it to an absolute (full) path.
# os.path.dirname() strips the filename, leaving just the folder.
# Result: _HERE = the folder where main.py lives, e.g. "C:/projects/cardodge"
# We use _HERE later to build paths to music/, leaderboard.json, etc.
# This guarantees the game finds its files no matter where you run it from.

sys.path.insert(0, _HERE)
# Adds _HERE to the front of Python's module search path.
# This means "from racer import ..." will look in the same folder as main.py first,
# preventing conflicts with installed packages that might have the same name.

from racer import (
    # Importing constants and classes from racer.py
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    # SCREEN_WIDTH, SCREEN_HEIGHT — pixel dimensions of the game window
    # FPS — target frames per second (e.g. 60)
    INITIAL_SPEED, COIN_SPEED_MILESTONE, COIN_SPEED_BOOST, TIME_SPEED_BOOST,
    # INITIAL_SPEED       — how fast the road scrolls at game start
    # COIN_SPEED_MILESTONE— how many coins must be collected to trigger a speed boost
    # COIN_SPEED_BOOST    — how much speed is added when the coin milestone is hit
    # TIME_SPEED_BOOST    — how much speed is added each second automatically
    DIFFICULTY, POWERUP_DURATION,
    # DIFFICULTY      — a dict of difficulty presets: {"easy": {...}, "normal": {...}, "hard": {...}}
    # POWERUP_DURATION— a dict of how many frames each power-up lasts: {"nitro": 180, ...}
    BLACK, WHITE, RED, YELLOW, GREEN,
    # Named color tuples, e.g. BLACK = (0, 0, 0), WHITE = (255, 255, 255)
    Player, Enemy, Coin, Obstacle, PowerUp, NitroStrip,
    # Sprite classes:
    # Player     — the car the user controls
    # Enemy      — oncoming traffic cars
    # Coin       — collectible coins on the road
    # Obstacle   — hazards: oil spills, speed bumps, barriers
    # PowerUp    — collectible power-up items
    # NitroStrip — a speed-boost strip painted on the road
)
from ui import (
    # Importing all screen-drawing functions from ui.py
    draw_road, draw_hud,
    # draw_road — draws the scrolling road background each frame
    # draw_hud  — draws the heads-up display (score, coins, speed, power-up status)
    draw_main_menu, draw_settings, draw_leaderboard, draw_game_over,
    # draw_main_menu   — renders the main menu and returns clickable button rects
    # draw_settings    — renders the settings screen and returns button rects
    # draw_leaderboard — renders the leaderboard screen and returns button rects
    # draw_game_over   — renders the game-over screen and returns button rects
    username_entry,
    # username_entry — shows a text-input screen so the player can type their name
)
from persistence import (
    # Importing save/load helpers from persistence.py
    load_leaderboard, add_entry,
    # load_leaderboard — reads leaderboard.json and returns a list of score entries
    # add_entry        — appends a new score to leaderboard.json and sorts/trims it
    load_settings, save_settings,
    # load_settings — reads settings.json and returns a dict of user preferences
    # save_settings — writes the current settings dict back to settings.json
)

# ============================================================
#  Pygame Init
# ============================================================
pygame.init()
# Initializes ALL pygame subsystems (display, font, joystick, etc.) at once.
# Must be called before using any other pygame feature.

pygame.mixer.init()
# Separately initializes the audio mixer subsystem.
# Needed before loading or playing any sounds/music.

DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
# Creates the game window with our desired resolution.
# Returns a Surface object — the canvas we draw everything onto each frame.
# SCREEN_WIDTH and SCREEN_HEIGHT come from racer.py (e.g. 400 x 700).

pygame.display.set_caption("Car Dodge — TSIS 3")
# Sets the text shown in the window's title bar.

clock = pygame.time.Clock()
# Creates a Clock object used to control how fast the game loop runs.
# We call clock.tick(FPS) each frame to cap speed at FPS frames per second.

# ============================================================
#  Load settings once at startup
# ============================================================
settings = load_settings()
# Reads settings.json from disk and returns a dict like:
# {"sound": True, "car_color": "blue", "difficulty": "normal"}
# If the file doesn't exist, load_settings() returns safe defaults.
# We keep `settings` as a plain dict and mutate it throughout the session.


# ============================================================
#  Audio helpers
# ============================================================
def _try_load_sound(name):
    # Helper function: safely loads a sound effect file.
    # Returns a pygame.mixer.Sound object if successful, or None if not.
    # The leading underscore _ signals "private/internal — don't call this from outside".
    path = os.path.join(_HERE, "music", name)
    # Builds the full path to the sound file, e.g. "C:/projects/cardodge/music/crash.wav"
    # os.path.join handles the slash differences between Windows (\) and Mac/Linux (/).
    if os.path.exists(path):
        # Only try to load if the file actually exists on disk.
        # This prevents a crash if the user deleted the music folder.
        try:
            return pygame.mixer.Sound(path)
            # Load the .wav file into memory as a Sound object.
            # Sound objects can be played with .play(), stopped with .stop(), etc.
        except pygame.error:
            pass
            # If pygame can't decode the file (wrong format, corrupt, etc.),
            # silently ignore the error and fall through to return None.
    return None
    # Return None if the file doesn't exist or failed to load.
    # Callers must check: "if crash_snd and settings['sound']: crash_snd.play()"


def _play_music():
    # Starts the background music looping.
    # Uses pygame.mixer.music (streaming) instead of Sound (in-memory)
    # because music files are large and don't need to be loaded all at once.
    if not settings["sound"]:
        return
        # If sound is disabled in settings, do nothing and return immediately.
    path = os.path.join(_HERE, "music", "background.wav")
    # Build the path to the background music file.
    if os.path.exists(path):
        # Only proceed if the file exists.
        try:
            pygame.mixer.music.load(path)
            # Load the music file into the streaming player.
            # Only one music track can be loaded at a time (replaces any previous).
            pygame.mixer.music.set_volume(0.5)
            # Set playback volume to 50% (range 0.0 – 1.0).
            pygame.mixer.music.play(-1)
            # Start playback. -1 means loop forever.
        except pygame.error:
            pass
            # If the file can't be loaded/played, silently skip it.


def _stop_music():
    # Stops the background music if it's playing.
    # Called on crash, game over, or when the user turns sound off.
    try:
        pygame.mixer.music.stop()
        # Immediately halts music playback.
    except pygame.error:
        pass
        # Ignore errors (e.g. if no music was ever loaded).


crash_snd = _try_load_sound("crash.wav")
# Load the crash sound effect at startup (once).
# _try_load_sound returns None if the file is missing, so crash_snd may be None.
# We check for None before playing: "if crash_snd and settings['sound']: crash_snd.play()"


# ============================================================
#  Game State Machine
# ============================================================
# A state machine controls which "screen" is currently active.
# Only one state is active at any moment; each state handles its own
# drawing, events, and logic, then sets `state` to transition to the next screen.

STATE_MENU        = "menu"        # The main menu screen
STATE_SETTINGS    = "settings"    # The settings/options screen
STATE_LEADERBOARD = "leaderboard" # The high-score leaderboard screen
STATE_PLAYING     = "playing"     # The actual gameplay
STATE_GAMEOVER    = "gameover"    # The game-over / results screen

state          = STATE_MENU
# Start the game at the main menu when the program launches.

player_name    = "Player"
# Default username if the player skips the name-entry screen.
# This gets replaced by whatever the player types in username_entry().

menu_buttons   = {}  # Dict of button Rects returned by draw_main_menu(); starts empty
set_buttons    = {}  # Dict of button Rects returned by draw_settings(); starts empty
lb_buttons     = {}  # Dict of button Rects returned by draw_leaderboard(); starts empty
go_buttons     = {}  # Dict of button Rects returned by draw_game_over(); starts empty
# Each draw_*() function returns a dict like {"play": Rect(...), "quit": Rect(...)}
# We store them here so the event-handling code can check mouse clicks against them.

# run-result cache for game-over / leaderboard submission
_last_score    = 0  # Score from the most recently finished game
_last_coins    = 0  # Coins collected in the most recently finished game
_last_distance = 0  # Distance traveled in the most recently finished game
# These are written just before transitioning to STATE_GAMEOVER
# and read by draw_game_over() to display the results.


# ============================================================
#  Helper: build a fresh game session
# ============================================================
def new_game():
    """Return all mutable game objects for a fresh run."""
    # This function creates and returns every piece of game state needed
    # for a single play session. Calling it again resets everything cleanly.
    # It returns a dict `G` that the main loop reads and writes every frame.

    diff_key = settings.get("difficulty", "normal")
    # Read the difficulty setting; default to "normal" if missing.

    diff     = DIFFICULTY[diff_key]
    # Look up the full difficulty preset dict, e.g.:
    # {"initial_speed": 5, "enemy_count": 3, "obstacle_rate": 60}

    speed = [diff["initial_speed"]]
    # Speed is stored as a one-element list [value] so it can be passed by reference
    # into sprite constructors (Player, Enemy, etc.) and mutated from anywhere.
    # If we used a plain integer, changing it in one place wouldn't affect others.

    score = [0]
    # Same trick — a list so score can be mutated by Enemy or other sprites.

    player    = Player(speed_ref=speed, car_color=settings.get("car_color", "blue"))
    # Create the player's car sprite.
    # speed_ref=speed passes the reference so the player's movement speed
    # automatically tracks whatever speed[0] is at any given frame.
    # car_color picks the sprite image based on user's color preference.

    enemies   = pygame.sprite.Group(*[Enemy(speed_ref=speed, score_ref=score)
                                      for _ in range(diff["enemy_count"])])
    # Create `enemy_count` Enemy sprites (e.g. 3 on Normal difficulty)
    # using a list comprehension, then unpack them into a sprite Group.
    # The * unpacks the list: Group(e1, e2, e3) instead of Group([e1, e2, e3]).
    # Each enemy gets speed_ref and score_ref so it can update speed and score.

    coins     = pygame.sprite.Group(Coin(speed_ref=speed))
    # Start with one coin on screen. Coins respawn automatically when collected.

    obstacles = pygame.sprite.Group()
    # Empty group at start; obstacles spawn over time via the obs_timer logic.

    powerups  = pygame.sprite.Group()
    # Empty group at start; power-ups spawn on a random timer.

    nitros    = pygame.sprite.Group()
    # Empty group at start; nitro strips spawn on a random timer.

    players   = pygame.sprite.GroupSingle(player)
    # GroupSingle holds exactly one sprite — the player.
    # Not currently used for collision detection in this file,
    # but useful if ui.py or racer.py needs a group reference to the player.

    all_spr   = pygame.sprite.Group(player, *enemies.sprites(), *coins.sprites())
    # A "catch-all" group with all active sprites at game start.
    # *enemies.sprites() unpacks the enemy Group into individual sprites.
    # Note: obstacles, powerups, nitros are managed in their own groups
    # and are NOT added here (they're drawn manually in the main loop).

    return {
        # ---- Core numeric state ----
        "speed":         speed,          # [float] — current road scroll / enemy speed
        "score":         score,          # [int]   — score from enemy events (unused directly in HUD here)
        "coins_total":   0,              # int     — total coins collected this run
        "distance":      0,              # int     — frames traveled (divided by 10 for score)

        # ---- Sprite groups ----
        "player":        player,         # Player sprite
        "enemies":       enemies,        # Group of Enemy sprites
        "coins":         coins,          # Group of Coin sprites
        "obstacles":     obstacles,      # Group of Obstacle sprites
        "powerups":      powerups,       # Group of PowerUp sprites
        "nitros":        nitros,         # Group of NitroStrip sprites
        "players":       players,        # GroupSingle(player)
        "all_spr":       all_spr,        # Combined group (player+enemies+coins)

        # ---- Speed milestone tracking ----
        "next_milestone": COIN_SPEED_MILESTONE,
        # The coin count at which the next speed boost triggers.
        # Incremented by COIN_SPEED_MILESTONE each time it's hit.

        # ---- Power-up state ----
        "active_pu":     None,           # Which power-up is active: "nitro"|"shield"|"repair"|None
        "pu_timer":      0,              # Frames remaining for the active timed power-up

        # ---- Road scroll ----
        "scroll_y":      0,              # Current vertical scroll offset for the road background

        # ---- Spawn timers ----
        "obs_timer":     0,              # Counts up; spawns an obstacle when it hits obstacle_rate
        "pu_spawn_timer":random.randint(300, 600),
        # Random delay (300-600 frames) before the first power-up spawns.
        "nitro_timer":   random.randint(400, 800),
        # Random delay (400-800 frames) before the first nitro strip spawns.

        # ---- Special effect timers ----
        "oil_timer":     0,              # Frames remaining for the oil-spill slow effect
        "nitro_strip_timer": 0,          # Frames remaining for the nitro-strip speed boost

        # ---- Difficulty preset ----
        "diff":          diff,           # The full difficulty dict for this session
    }


INC_SPEED = pygame.USEREVENT + 1
# Define a custom pygame event type for "increase speed every second".
# pygame.USEREVENT is the base ID for user-defined events.
# Adding 1 gives us a unique ID that won't clash with built-in events.

pygame.time.set_timer(INC_SPEED, 1000)
# Tell pygame to fire an INC_SPEED event into the event queue every 1000ms (1 second).
# This is how we implement the "road gets faster over time" mechanic
# without having to manually track elapsed milliseconds in the game loop.

# ---- Initial game state (placeholder until Play is pressed) -----------------
G = new_game()
# Create a default game state dict at startup.
# This G is thrown away and replaced by a fresh new_game() call when the player
# actually hits Play — it's just here so G is always defined before the main loop.

# ============================================================
#  Main Loop
# ============================================================
_play_music()
# Start the background music before entering the main loop.

while True:
    # Infinite loop — runs once per frame until the game is quit.
    # Each iteration: handle events → update state → draw → flip display.

    dt = clock.tick(FPS)
    # Wait until the frame duration (1000ms / FPS) has elapsed, then return
    # the actual milliseconds since the last tick (delta time).
    # This caps the game at FPS frames per second.
    # We store dt but don't actually use it for movement (speed[0] is frame-based).

    # ================================================================
    #  MENU
    # ================================================================
    if state == STATE_MENU:
        # We're on the main menu screen. Draw it and handle clicks.

        menu_buttons = draw_main_menu(DISPLAYSURF)
        # Draw the main menu onto the display surface.
        # Returns a dict of pygame.Rect objects for each button:
        # {"play": Rect, "leaderboard": Rect, "settings": Rect, "quit": Rect}
        # We store it so the event loop below can test mouse clicks.

        pygame.display.flip()
        # Push the freshly drawn frame to the actual screen.
        # Without this, the player would never see the menu.

        for event in pygame.event.get():
            # Process every event queued since the last frame.
            if event.type == QUIT:
                # User clicked the window's X button.
                save_settings(settings)
                # Save current settings to settings.json before exiting.
                pygame.quit(); sys.exit()
                # pygame.quit() shuts down all pygame subsystems.
                # sys.exit() terminates the Python process.

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # A left mouse button press occurred.
                pos = event.pos
                # event.pos is a (x, y) tuple of where the click happened.

                if menu_buttons["play"].collidepoint(pos):
                    # The click landed inside the Play button's rectangle.
                    player_name = username_entry(DISPLAYSURF, clock)
                    # Show the name-entry screen; blocks until the player presses Enter.
                    # Returns whatever string the player typed (or default "Player").
                    G = new_game()
                    # Create a completely fresh game session.
                    _play_music()
                    # Restart background music (in case it was stopped).
                    state = STATE_PLAYING
                    # Transition to the gameplay state next frame.

                elif menu_buttons["leaderboard"].collidepoint(pos):
                    state = STATE_LEADERBOARD
                    # Go to the leaderboard screen.

                elif menu_buttons["settings"].collidepoint(pos):
                    state = STATE_SETTINGS
                    # Go to the settings screen.

                elif menu_buttons["quit"].collidepoint(pos):
                    save_settings(settings)
                    # Save before quitting from the menu too.
                    pygame.quit(); sys.exit()

        continue
        # Skip the rest of the loop body (gameplay code) for this frame.
        # `continue` jumps back to `while True:` immediately.

    # ================================================================
    #  SETTINGS
    # ================================================================
    if state == STATE_SETTINGS:
        # We're on the settings screen. Draw it and handle clicks.

        set_buttons = draw_settings(DISPLAYSURF, settings)
        # Draw the settings screen, passing current settings so checkboxes/
        # highlights reflect the current state. Returns button Rects.

        pygame.display.flip()
        # Show the drawn frame.

        for event in pygame.event.get():
            if event.type == QUIT:
                save_settings(settings)
                pygame.quit(); sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                if set_buttons["back"].collidepoint(pos):
                    save_settings(settings)
                    # Persist any changes before leaving the settings screen.
                    state = STATE_MENU
                    # Return to the main menu.

                elif set_buttons["sound"].collidepoint(pos):
                    settings["sound"] = not settings["sound"]
                    # Toggle sound on/off (boolean flip).
                    if settings["sound"]:
                        _play_music()
                        # If sound was just turned ON, start the music.
                    else:
                        _stop_music()
                        # If sound was just turned OFF, stop the music.

                for col in ("blue", "red", "yellow"):
                    # Check each car color button.
                    if set_buttons[f"color_{col}"].collidepoint(pos):
                        settings["car_color"] = col
                        # Update the preferred car color. Applied on next new_game().

                for diff in ("easy", "normal", "hard"):
                    # Check each difficulty button.
                    if set_buttons[f"diff_{diff}"].collidepoint(pos):
                        settings["difficulty"] = diff
                        # Update the preferred difficulty. Applied on next new_game().
        continue

    # ================================================================
    #  LEADERBOARD
    # ================================================================
    if state == STATE_LEADERBOARD:
        # We're on the leaderboard screen.

        entries    = load_leaderboard()
        # Read the current leaderboard from leaderboard.json every frame.
        # Slightly inefficient (reads disk each frame) but the list is small
        # and this keeps the data fresh if multiple instances were running.

        lb_buttons = draw_leaderboard(DISPLAYSURF, entries)
        # Draw the leaderboard table and return button Rects (just "back" here).

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == QUIT:
                save_settings(settings)
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if lb_buttons["back"].collidepoint(event.pos):
                    state = STATE_MENU
                    # Return to the main menu.
        continue

    # ================================================================
    #  GAME OVER
    # ================================================================
    if state == STATE_GAMEOVER:
        # We're on the game-over / results screen.

        go_buttons = draw_game_over(DISPLAYSURF, _last_score, _last_coins, _last_distance)
        # Draw the game-over screen with the final stats.
        # Returns button Rects: {"retry": Rect, "menu": Rect}

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == QUIT:
                save_settings(settings)
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                if go_buttons["retry"].collidepoint(pos):
                    G = new_game()
                    # Fresh game session with the same player name.
                    _play_music()
                    state = STATE_PLAYING
                    # Jump straight back into gameplay.

                elif go_buttons["menu"].collidepoint(pos):
                    state = STATE_MENU
                    # Go back to the main menu (player might change name/settings).
        continue

    # ================================================================
    #  PLAYING  — everything below runs only during active gameplay
    # ================================================================

    # ---- Unpack game state ----
    # Pull frequently-used references out of G for cleaner code.
    # These are not copies — they point to the same objects inside G.
    speed         = G["speed"]         # [float] list — current game speed
    score         = G["score"]         # [int] list   — enemy-event score
    player        = G["player"]        # Player sprite
    enemies       = G["enemies"]       # Group of Enemy sprites
    coins         = G["coins"]         # Group of Coin sprites
    obstacles     = G["obstacles"]     # Group of Obstacle sprites
    powerups      = G["powerups"]      # Group of PowerUp sprites
    nitros        = G["nitros"]        # Group of NitroStrip sprites
    diff          = G["diff"]          # Difficulty preset dict

    # ---- Events ----
    for event in pygame.event.get():
        # Process all queued events for this frame.

        if event.type == QUIT:
            save_settings(settings)
            pygame.quit(); sys.exit()

        if event.type == INC_SPEED:
            # Our custom timer fires every 1 second (set up with set_timer above).
            speed[0] += TIME_SPEED_BOOST
            # Increase road speed by the per-second boost constant.
            # This makes the game progressively harder the longer you survive.

            # Difficulty scaling: add obstacles more often as speed grows
            G["obs_timer"] = max(20, G["obs_timer"] - 2)
            # Decrease the obstacle spawn interval by 2 frames each second,
            # but never go below 20 frames (cap) so obstacles don't stack up infinitely.
            # NOTE: This line has a subtle bug — it's subtracting from the current
            # timer value rather than from diff["obstacle_rate"]. The intent is to
            # make obstacle_rate shrink over time, but as written it only affects
            # the current timer, not future spawn intervals.

    # ---- Timers / Spawning ----
    G["obs_timer"] += 1
    # Increment the obstacle spawn counter by 1 each frame.

    if G["obs_timer"] >= diff["obstacle_rate"]:
        # When the counter reaches the spawn interval (e.g. every 60 frames = 1 second at 60 FPS)...
        G["obs_timer"] = 0
        # ...reset the counter...
        obs = Obstacle(speed_ref=speed)
        # ...create a new Obstacle sprite at a random lane and type (oil/bump/barrier)...
        obstacles.add(obs)
        # ...and add it to the obstacles group so it gets updated and drawn.

    G["pu_spawn_timer"] -= 1
    # Count down toward the next power-up spawn.

    if G["pu_spawn_timer"] <= 0:
        # Timer expired — time to potentially spawn a power-up.
        G["pu_spawn_timer"] = random.randint(350, 700)
        # Reset to a new random interval (350-700 frames ≈ 6-12 seconds at 60 FPS).
        if len(powerups) == 0:
            # Only spawn if there's no power-up already on screen.
            # This prevents multiple power-ups stacking up at once.
            powerups.add(PowerUp(speed_ref=speed))
            # Create a new random PowerUp sprite (nitro/shield/repair chosen randomly inside).

    G["nitro_timer"] -= 1
    # Count down toward the next nitro strip spawn.

    if G["nitro_timer"] <= 0:
        # Timer expired — spawn a nitro strip on the road.
        G["nitro_timer"] = random.randint(400, 900)
        # Reset to a new random interval.
        nitros.add(NitroStrip(speed_ref=speed))
        # Create a new NitroStrip sprite (a painted stripe across a lane).

    # Active power-up countdown
    if G["active_pu"] == "nitro" and G["pu_timer"] > 0:
        # The nitro power-up is active and has time remaining.
        G["pu_timer"] -= 1
        # Tick the timer down by one frame.
        if G["pu_timer"] <= 0:
            # Timer just ran out — nitro expires.
            G["active_pu"] = None
            # Clear the active power-up slot.
            speed[0] = max(diff["initial_speed"], speed[0] - 3)
            # Remove the +3 speed that was added when nitro activated,
            # but never go below the difficulty's base speed.

    # Oil slow countdown — restore player speed when timer expires
    if G["oil_timer"] > 0:
        # The player is currently slowed by an oil spill.
        G["oil_timer"] -= 1
        # Tick down one frame.
        if G["oil_timer"] == 0:
            # Slow effect just ended.
            player.slowed = False
            # Tell the player sprite it's no longer slowed (removes the movement cap).
            speed[0] = min(speed[0] + 2, speed[0] + 2)  # restore road scroll speed
            # NOTE: this line is effectively "speed[0] = speed[0] + 2" — the min()
            # is redundant (both arguments are identical). The intent is to undo the
            # -2 penalty applied when the oil was hit, but the cap doesn't work as intended.

    # Nitro strip boost countdown — restore speed when timer expires
    if G["nitro_strip_timer"] > 0:
        # The player drove over a nitro strip and is getting a speed boost.
        G["nitro_strip_timer"] -= 1
        # Tick down one frame.
        if G["nitro_strip_timer"] == 0:
            # Boost just ended.
            player.nitro_strip_active = False
            # Clear the flag on the player sprite.
            speed[0] = max(diff["initial_speed"], speed[0] - 2)
            # Undo the +2 speed that was added when the strip was hit,
            # never going below the base speed.

    # ---- Scroll ----
    G["scroll_y"] = (G["scroll_y"] + int(speed[0])) % (SCREEN_HEIGHT + 60)
    # Advance the road scroll position by speed[0] pixels each frame.
    # Wrapping with % (SCREEN_HEIGHT + 60) creates an infinite seamless loop.
    # The +60 gives a small buffer so the road tile seam isn't visible.

    # ---- Distance ----
    G["distance"] += 1
    # Increment distance counter by 1 every frame.
    # Distance is divided by 10 when added to the score (so 600 frames = 60 score points).
    # This rewards players who survive longer even if they avoid coins.

    # ---- Draw ----
    draw_road(DISPLAYSURF, G["scroll_y"])
    # Draw the scrolling road background first (bottom layer).
    # Everything else is drawn on top of it.

    # Nitro strips
    for ns in nitros:
        # Iterate over every NitroStrip sprite currently on screen.
        ns.move()
        # Move the strip downward by speed[0] pixels (scrolls with the road).
        DISPLAYSURF.blit(ns.image, ns.rect)
        # Draw the strip's image at its current position on the display surface.

    # Nitro strip collision — boost speed for 2 seconds
    hit_nitro = pygame.sprite.spritecollide(player, nitros, True)
    # Check if the player overlaps any nitro strip.
    # True = kill (remove from group) the strip on collision.
    # Returns a list of all NitroStrip sprites that were hit.

    for ns in hit_nitro:
        # For each strip the player just drove over...
        if not getattr(player, "nitro_strip_active", False):
            # ...only apply if a strip boost isn't already active
            # (getattr with default False handles the case where the attribute doesn't exist yet).
            player.nitro_strip_active = True
            # Set the flag so we don't stack boosts.
            speed[0] += 2
            # Add +2 to road speed immediately.
            G["nitro_strip_timer"] = 2 * FPS   # 2 second boost
            # Set the countdown: 2 seconds × 60 FPS = 120 frames.

    # Obstacles
    for obs in obstacles:
        # Iterate over every active Obstacle sprite.
        obs.move()
        # Move it downward by speed[0] pixels.
        DISPLAYSURF.blit(obs.image, obs.rect)
        # Draw it on screen.

    # Powerups
    for pu in powerups:
        # Iterate over every active PowerUp sprite.
        pu.move()
        # Move it downward.
        DISPLAYSURF.blit(pu.image, pu.rect)
        # Draw it.

    # Enemies
    for e in enemies:
        # Iterate over every Enemy sprite.
        e.move()
        # Move the enemy (they also move side-to-side and come from the top).
        DISPLAYSURF.blit(e.image, e.rect)
        # Draw the enemy car.

    # Coins
    for c in coins:
        # Iterate over every Coin sprite.
        c.move()
        # Move it downward.
        DISPLAYSURF.blit(c.image, c.rect)
        # Draw it.

    # Player
    player.move()
    # Update the player's position based on keyboard input and speed cap.
    DISPLAYSURF.blit(player.image, player.rect)
    # Draw the player's car on top of everything else drawn so far.

    # ---- Coin collection ----
    hit_coins = pygame.sprite.spritecollide(player, coins, False)
    # Check if the player overlaps any coin.
    # False = do NOT remove the coin on collision (we handle removal manually below via _respawn).
    # Returns a list of Coin sprites that were hit.

    for coin in hit_coins:
        # For each coin the player touched this frame...
        G["coins_total"] += coin.value
        # Add the coin's value (e.g. 1) to the running coin total.

        if G["coins_total"] >= G["next_milestone"]:
            # If the total coins collected crossed the next milestone...
            speed[0]          += COIN_SPEED_BOOST
            # ...give a speed boost as a reward...
            G["next_milestone"] += COIN_SPEED_MILESTONE
            # ...and move the milestone target forward.

        coin._respawn()
        # Instead of destroying the coin, teleport it back to a random position
        # at the top of the screen so coins are always available on the road.

    # ---- Power-up collection ----
    hit_pu = pygame.sprite.spritecollide(player, powerups, True)
    # Check if the player overlaps any power-up.
    # True = remove the power-up from the group when collected.

    for pu in hit_pu:
        # For each power-up the player just picked up...

        # Only one active at a time: cancel previous nitro first
        if G["active_pu"] == "nitro":
            speed[0] = max(diff["initial_speed"], speed[0] - 3)
            # Undo the speed boost from the previous nitro before applying the new one.

        G["active_pu"] = pu.kind
        # Record which power-up is now active ("nitro", "shield", or "repair").

        if pu.kind == "nitro":
            speed[0]    += 3
            # Immediately boost speed by 3.
            G["pu_timer"] = POWERUP_DURATION["nitro"]
            # Set the countdown timer so the boost expires after the defined duration.

        elif pu.kind == "shield":
            player.has_shield = True
            # Activate the shield flag on the player. The shield absorbs one hit.
            G["pu_timer"]     = 0
            # Shield has no timed duration — it lasts until hit (no timer needed).

        elif pu.kind == "repair":
            # Repair is a one-time instant effect: clear all current obstacles.
            obstacles.empty()
            # Remove every obstacle sprite from the group at once.
            G["active_pu"] = None
            # Repair is instant, so no "active" state remains afterward.

    # ---- Obstacle collision ----
    hit_obs = pygame.sprite.spritecollide(player, obstacles, False)
    # Check if the player overlaps any obstacle.
    # False = don't auto-remove; we handle removal selectively below.

    for obs in hit_obs:
        # For each obstacle the player is currently touching...

        if obs.obs_type == "oil":
            # An oil spill — it slows the player temporarily but doesn't end the game.

            if not getattr(player, "slowed", False) and not player.has_shield:
                # Only apply the slow if the player isn't already slowed AND has no shield.
                player.slowed  = True
                # Flag the player as slowed (limits movement speed in Player.move()).
                player.spd_cap = 2          # movement capped to 2px while slowed
                # Set the max pixels-per-frame the player can move horizontally.
                G["oil_timer"] = 3 * FPS    # 3 seconds
                # Start a 3-second countdown (3 × 60 = 180 frames).
                speed[0]       = max(diff["initial_speed"] - 1, speed[0] - 2)
                # Slow the road scroll speed too, but not below base - 1.
                obs.kill()                  # remove the spill once hit
                # Destroy the oil spill sprite so it can't trigger again.

        elif obs.obs_type in ("bump", "barrier"):
            # A speed bump or barrier — these are deadly unless the shield is active.

            if player.has_shield:
                player.has_shield = False
                # Shield absorbs the hit — deactivate it.
                G["active_pu"]    = None
                # Clear the active power-up slot since shield is consumed.
                obs.kill()
                # Also remove the obstacle so it doesn't trigger every frame.
            else:
                # No shield — this is a crash. End the game.
                _stop_music()
                # Stop background music immediately.
                if crash_snd and settings["sound"]:
                    crash_snd.play()
                # Play crash sound effect if available and sound is on.
                time.sleep(0.8)
                # Pause for 0.8 seconds so the player registers the crash visually.
                _last_score    = score[0] + G["coins_total"] + G["distance"] // 10
                # Calculate final score: enemy-event score + coins + distance bonus.
                # distance // 10 converts raw frame count to a smaller point value.
                _last_coins    = G["coins_total"]
                # Cache coins for the game-over screen.
                _last_distance = G["distance"]
                # Cache distance for the game-over screen.
                add_entry(player_name, _last_score, _last_distance, _last_coins)
                # Save this run to leaderboard.json immediately.
                state = STATE_GAMEOVER
                # Transition to the game-over screen next frame.
                break
                # Stop processing more obstacle collisions — game is already over.

    if state == STATE_GAMEOVER:
        pygame.display.flip()
        # Flush the last drawn frame to the screen before the loop continues
        # to STATE_GAMEOVER handling (which redraws the game-over screen).
        continue
        # Skip the rest of this frame's gameplay code.

    # ---- Enemy collision ----
    if pygame.sprite.spritecollideany(player, enemies):
        # Check if the player is touching ANY enemy (returns the first hit or None).
        # We use spritecollideany (not spritecollide) because we only need a yes/no
        # to decide shield vs crash, before getting the full list below if shielded.

        if player.has_shield:
            player.has_shield = False
            # Shield absorbs the enemy collision.
            G["active_pu"]    = None
            # Deactivate the shield slot.

            # push colliding enemy away
            for e in pygame.sprite.spritecollide(player, enemies, False):
                e._place_at_top()
                # Teleport each colliding enemy back to the top of the screen.
                # This prevents repeated frame-by-frame collisions with the same enemy.

        else:
            # No shield — crash!
            _stop_music()
            if crash_snd and settings["sound"]:
                crash_snd.play()
            time.sleep(0.8)
            # 0.8-second pause (same as obstacle crash above).
            _last_score    = score[0] + G["coins_total"] + G["distance"] // 10
            _last_coins    = G["coins_total"]
            _last_distance = G["distance"]
            add_entry(player_name, _last_score, _last_distance, _last_coins)
            state = STATE_GAMEOVER
            # (No `break` needed here — this is an `if` block, not a `for` loop.)

    # ---- HUD ----
    total_score = score[0] + G["coins_total"] + G["distance"] // 10
    # Recalculate the combined score every frame for live display.
    # This is the same formula used on game-over; it counts everything.

    draw_hud(
        DISPLAYSURF,
        # The surface to draw the HUD onto (drawn last = on top of everything).
        score    = total_score,       # Combined score shown in top-left
        coins    = G["coins_total"],  # Coin counter
        distance = G["distance"],     # Distance traveled (raw frames)
        speed    = speed[0],          # Current road speed (shown as km/h or similar)
        active_powerup = G["active_pu"],        # Which power-up icon to highlight
        powerup_timer  = G["pu_timer"],          # Frames remaining (for nitro bar)
        fps            = FPS,                    # Target FPS (used to convert timer to seconds)
        has_shield     = player.has_shield,      # Whether shield icon should be lit up
        nitro_active   = G["active_pu"] == "nitro",  # True/False for nitro indicator
        oil_timer      = G["oil_timer"],         # Frames of oil slow remaining (for HUD icon)
        nitro_strip_timer = G["nitro_strip_timer"],  # Frames of strip boost remaining
    )

    pygame.display.flip()
    # Swap the back buffer to the screen — shows everything drawn this frame.
    # This is the last thing we do each frame; after this, the loop restarts.