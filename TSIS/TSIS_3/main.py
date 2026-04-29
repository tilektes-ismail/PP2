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

import pygame, sys, os, time, random
from pygame.locals import QUIT

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from racer import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    INITIAL_SPEED, COIN_SPEED_MILESTONE, COIN_SPEED_BOOST, TIME_SPEED_BOOST,
    DIFFICULTY, POWERUP_DURATION,
    BLACK, WHITE, RED, YELLOW, GREEN,
    Player, Enemy, Coin, Obstacle, PowerUp, NitroStrip,
)
from ui import (
    draw_road, draw_hud,
    draw_main_menu, draw_settings, draw_leaderboard, draw_game_over,
    username_entry,
)
from persistence import (
    load_leaderboard, add_entry,
    load_settings, save_settings,
)

# ============================================================
#  Pygame Init
# ============================================================
pygame.init()
pygame.mixer.init()

DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Car Dodge — TSIS 3")
clock = pygame.time.Clock()

# ============================================================
#  Load settings once at startup
# ============================================================
settings = load_settings()


# ============================================================
#  Audio helpers
# ============================================================
def _try_load_sound(name):
    path = os.path.join(_HERE, "music", name)
    if os.path.exists(path):
        try:
            return pygame.mixer.Sound(path)
        except pygame.error:
            pass
    return None


def _play_music():
    if not settings["sound"]:
        return
    path = os.path.join(_HERE, "music", "background.wav")
    if os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass


def _stop_music():
    try:
        pygame.mixer.music.stop()
    except pygame.error:
        pass


crash_snd = _try_load_sound("crash.wav")


# ============================================================
#  Game State Machine
# ============================================================
STATE_MENU        = "menu"
STATE_SETTINGS    = "settings"
STATE_LEADERBOARD = "leaderboard"
STATE_PLAYING     = "playing"
STATE_GAMEOVER    = "gameover"

state          = STATE_MENU
player_name    = "Player"
menu_buttons   = {}
set_buttons    = {}
lb_buttons     = {}
go_buttons     = {}

# run-result cache for game-over / leaderboard submission
_last_score    = 0
_last_coins    = 0
_last_distance = 0


# ============================================================
#  Helper: build a fresh game session
# ============================================================
def new_game():
    """Return all mutable game objects for a fresh run."""
    diff_key = settings.get("difficulty", "normal")
    diff     = DIFFICULTY[diff_key]

    speed = [diff["initial_speed"]]
    score = [0]

    player    = Player(speed_ref=speed, car_color=settings.get("car_color", "blue"))
    enemies   = pygame.sprite.Group(*[Enemy(speed_ref=speed, score_ref=score)
                                      for _ in range(diff["enemy_count"])])
    coins     = pygame.sprite.Group(Coin(speed_ref=speed))
    obstacles = pygame.sprite.Group()
    powerups  = pygame.sprite.Group()
    nitros    = pygame.sprite.Group()
    players   = pygame.sprite.GroupSingle(player)
    all_spr   = pygame.sprite.Group(player, *enemies.sprites(), *coins.sprites())

    return {
        "speed":         speed,
        "score":         score,
        "player":        player,
        "enemies":       enemies,
        "coins":         coins,
        "obstacles":     obstacles,
        "powerups":      powerups,
        "nitros":        nitros,
        "players":       players,
        "all_spr":       all_spr,
        "coins_total":   0,
        "distance":      0,
        "next_milestone": COIN_SPEED_MILESTONE,
        "active_pu":     None,   # "nitro" | "shield" | "repair" | None
        "pu_timer":      0,
        "scroll_y":      0,
        "obs_timer":     0,
        "pu_spawn_timer":random.randint(300, 600),
        "nitro_timer":   random.randint(400, 800),
        "oil_timer":     0,      # frames remaining for oil slow effect
        "nitro_strip_timer": 0,  # frames remaining for nitro strip boost
        "diff":          diff,
    }


INC_SPEED = pygame.USEREVENT + 1
pygame.time.set_timer(INC_SPEED, 1000)

# ---- Initial game state (placeholder until Play is pressed) -----------------
G = new_game()

# ============================================================
#  Main Loop
# ============================================================
_play_music()

while True:
    dt = clock.tick(FPS)

    # ================================================================
    #  MENU
    # ================================================================
    if state == STATE_MENU:
        menu_buttons = draw_main_menu(DISPLAYSURF)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == QUIT:
                save_settings(settings)
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if menu_buttons["play"].collidepoint(pos):
                    player_name = username_entry(DISPLAYSURF, clock)
                    G = new_game()
                    _play_music()
                    state = STATE_PLAYING
                elif menu_buttons["leaderboard"].collidepoint(pos):
                    state = STATE_LEADERBOARD
                elif menu_buttons["settings"].collidepoint(pos):
                    state = STATE_SETTINGS
                elif menu_buttons["quit"].collidepoint(pos):
                    save_settings(settings)
                    pygame.quit(); sys.exit()
        continue

    # ================================================================
    #  SETTINGS
    # ================================================================
    if state == STATE_SETTINGS:
        set_buttons = draw_settings(DISPLAYSURF, settings)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == QUIT:
                save_settings(settings)
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if set_buttons["back"].collidepoint(pos):
                    save_settings(settings)
                    state = STATE_MENU
                elif set_buttons["sound"].collidepoint(pos):
                    settings["sound"] = not settings["sound"]
                    if settings["sound"]:
                        _play_music()
                    else:
                        _stop_music()
                for col in ("blue", "red", "yellow"):
                    if set_buttons[f"color_{col}"].collidepoint(pos):
                        settings["car_color"] = col
                for diff in ("easy", "normal", "hard"):
                    if set_buttons[f"diff_{diff}"].collidepoint(pos):
                        settings["difficulty"] = diff
        continue

    # ================================================================
    #  LEADERBOARD
    # ================================================================
    if state == STATE_LEADERBOARD:
        entries    = load_leaderboard()
        lb_buttons = draw_leaderboard(DISPLAYSURF, entries)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == QUIT:
                save_settings(settings)
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if lb_buttons["back"].collidepoint(event.pos):
                    state = STATE_MENU
        continue

    # ================================================================
    #  GAME OVER
    # ================================================================
    if state == STATE_GAMEOVER:
        go_buttons = draw_game_over(DISPLAYSURF, _last_score, _last_coins, _last_distance)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == QUIT:
                save_settings(settings)
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if go_buttons["retry"].collidepoint(pos):
                    G = new_game()
                    _play_music()
                    state = STATE_PLAYING
                elif go_buttons["menu"].collidepoint(pos):
                    state = STATE_MENU
        continue

    # ================================================================
    #  PLAYING
    # ================================================================

    # ---- Unpack game state ----
    speed         = G["speed"]
    score         = G["score"]
    player        = G["player"]
    enemies       = G["enemies"]
    coins         = G["coins"]
    obstacles     = G["obstacles"]
    powerups      = G["powerups"]
    nitros        = G["nitros"]
    diff          = G["diff"]

    # ---- Events ----
    for event in pygame.event.get():
        if event.type == QUIT:
            save_settings(settings)
            pygame.quit(); sys.exit()
        if event.type == INC_SPEED:
            speed[0] += TIME_SPEED_BOOST
            # Difficulty scaling: add obstacles more often as speed grows
            G["obs_timer"] = max(20, G["obs_timer"] - 2)

    # ---- Timers / Spawning ----
    G["obs_timer"] += 1
    if G["obs_timer"] >= diff["obstacle_rate"]:
        G["obs_timer"] = 0
        obs = Obstacle(speed_ref=speed)
        obstacles.add(obs)

    G["pu_spawn_timer"] -= 1
    if G["pu_spawn_timer"] <= 0:
        G["pu_spawn_timer"] = random.randint(350, 700)
        if len(powerups) == 0:
            powerups.add(PowerUp(speed_ref=speed))

    G["nitro_timer"] -= 1
    if G["nitro_timer"] <= 0:
        G["nitro_timer"] = random.randint(400, 900)
        nitros.add(NitroStrip(speed_ref=speed))

    # Active power-up countdown
    if G["active_pu"] == "nitro" and G["pu_timer"] > 0:
        G["pu_timer"] -= 1
        if G["pu_timer"] <= 0:
            G["active_pu"] = None
            speed[0] = max(diff["initial_speed"], speed[0] - 3)

    # Oil slow countdown — restore player speed when timer expires
    if G["oil_timer"] > 0:
        G["oil_timer"] -= 1
        if G["oil_timer"] == 0:
            player.slowed = False
            speed[0] = min(speed[0] + 2, speed[0] + 2)  # restore road scroll speed

    # Nitro strip boost countdown — restore speed when timer expires
    if G["nitro_strip_timer"] > 0:
        G["nitro_strip_timer"] -= 1
        if G["nitro_strip_timer"] == 0:
            player.nitro_strip_active = False
            speed[0] = max(diff["initial_speed"], speed[0] - 2)

    # ---- Scroll ----
    G["scroll_y"] = (G["scroll_y"] + int(speed[0])) % (SCREEN_HEIGHT + 60)

    # ---- Distance ----
    G["distance"] += 1

    # ---- Draw ----
    draw_road(DISPLAYSURF, G["scroll_y"])

    # Nitro strips
    for ns in nitros:
        ns.move()
        DISPLAYSURF.blit(ns.image, ns.rect)

    # Nitro strip collision — boost speed for 2 seconds
    hit_nitro = pygame.sprite.spritecollide(player, nitros, True)
    for ns in hit_nitro:
        if not getattr(player, "nitro_strip_active", False):
            player.nitro_strip_active = True
            speed[0] += 2
            G["nitro_strip_timer"] = 2 * FPS   # 2 second boost

    # Obstacles
    for obs in obstacles:
        obs.move()
        DISPLAYSURF.blit(obs.image, obs.rect)

    # Powerups
    for pu in powerups:
        pu.move()
        DISPLAYSURF.blit(pu.image, pu.rect)

    # Enemies
    for e in enemies:
        e.move()
        DISPLAYSURF.blit(e.image, e.rect)

    # Coins
    for c in coins:
        c.move()
        DISPLAYSURF.blit(c.image, c.rect)

    # Player
    player.move()
    DISPLAYSURF.blit(player.image, player.rect)

    # ---- Coin collection ----
    hit_coins = pygame.sprite.spritecollide(player, coins, False)
    for coin in hit_coins:
        G["coins_total"] += coin.value
        if G["coins_total"] >= G["next_milestone"]:
            speed[0]          += COIN_SPEED_BOOST
            G["next_milestone"] += COIN_SPEED_MILESTONE
        coin._respawn()

    # ---- Power-up collection ----
    hit_pu = pygame.sprite.spritecollide(player, powerups, True)
    for pu in hit_pu:
        # Only one active at a time: cancel previous nitro first
        if G["active_pu"] == "nitro":
            speed[0] = max(diff["initial_speed"], speed[0] - 3)

        G["active_pu"] = pu.kind
        if pu.kind == "nitro":
            speed[0]    += 3
            G["pu_timer"] = POWERUP_DURATION["nitro"]
        elif pu.kind == "shield":
            player.has_shield = True
            G["pu_timer"]     = 0
        elif pu.kind == "repair":
            # Repair clears all current obstacles (one-time)
            obstacles.empty()
            G["active_pu"] = None

    # ---- Obstacle collision ----
    hit_obs = pygame.sprite.spritecollide(player, obstacles, False)
    for obs in hit_obs:
        if obs.obs_type == "oil":
            # Only apply if not already slowed and shield isn't active
            if not getattr(player, "slowed", False) and not player.has_shield:
                player.slowed  = True
                player.spd_cap = 2          # movement capped to 2px while slowed
                G["oil_timer"] = 3 * FPS    # 3 seconds
                speed[0]       = max(diff["initial_speed"] - 1, speed[0] - 2)
                obs.kill()                  # remove the spill once hit
        elif obs.obs_type in ("bump", "barrier"):
            if player.has_shield:
                player.has_shield = False
                G["active_pu"]    = None
                obs.kill()
            else:
                # Crash!
                _stop_music()
                if crash_snd and settings["sound"]:
                    crash_snd.play()
                time.sleep(0.8)
                _last_score    = score[0] + G["coins_total"] + G["distance"] // 10
                _last_coins    = G["coins_total"]
                _last_distance = G["distance"]
                add_entry(player_name, _last_score, _last_distance, _last_coins)
                state = STATE_GAMEOVER
                break

    if state == STATE_GAMEOVER:
        pygame.display.flip()
        continue

    # ---- Enemy collision ----
    if pygame.sprite.spritecollideany(player, enemies):
        if player.has_shield:
            player.has_shield = False
            G["active_pu"]    = None
            # push colliding enemy away
            for e in pygame.sprite.spritecollide(player, enemies, False):
                e._place_at_top()
        else:
            _stop_music()
            if crash_snd and settings["sound"]:
                crash_snd.play()
            time.sleep(0.8)
            _last_score    = score[0] + G["coins_total"] + G["distance"] // 10
            _last_coins    = G["coins_total"]
            _last_distance = G["distance"]
            add_entry(player_name, _last_score, _last_distance, _last_coins)
            state = STATE_GAMEOVER

    # ---- HUD ----
    total_score = score[0] + G["coins_total"] + G["distance"] // 10
    draw_hud(
        DISPLAYSURF,
        score    = total_score,
        coins    = G["coins_total"],
        distance = G["distance"],
        speed    = speed[0],
        active_powerup = G["active_pu"],
        powerup_timer  = G["pu_timer"],
        fps            = FPS,
        has_shield     = player.has_shield,
        nitro_active   = G["active_pu"] == "nitro",
        oil_timer      = G["oil_timer"],
        nitro_strip_timer = G["nitro_strip_timer"],
    )

    pygame.display.flip()
