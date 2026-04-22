#Imports
import pygame, sys
from pygame.locals import K_LEFT, K_RIGHT, QUIT
import random, time
import os

# Base directory so files load correctly from any working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#Initializing pygame and sound mixer
pygame.init()
pygame.mixer.init()

#Setting up FPS 
FPS = 60
FramePerSec = pygame.time.Clock()

#Defining colors as RGB tuples
BLUE  = (0, 0, 255)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 215, 0)  # ← ADDED: Color for coin

#Game variables
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
SPEED = 5
SCORE = 0
COINS = 0  # ← ADDED: Variable to track collected coins

#Setting up Fonts
font = pygame.font.SysFont("Verdana", 60)
font_small = pygame.font.SysFont("Verdana", 20)
game_over = font.render("Game Over", True, BLACK)

# Load background image
background = pygame.image.load(os.path.join(BASE_DIR, "images", "AnimatedStreet.png"))

#Create the display surface
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
DISPLAYSURF.fill(WHITE)
pygame.display.set_caption("Game")

# Load and play background music on infinite loop
pygame.mixer.music.load(os.path.join(BASE_DIR, "music", "background.wav"))
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.image = pygame.image.load(os.path.join(BASE_DIR, "images", "Enemy.png"))
        self.rect = self.image.get_rect()
        self.rect.center = (random.randint(40, SCREEN_WIDTH - 40), 0)

    def move(self):
        global SCORE
        self.rect.move_ip(0, SPEED)
        if self.rect.bottom > SCREEN_HEIGHT:
            SCORE += 1
            self.rect.top = 0
            self.rect.center = (random.randint(40, SCREEN_WIDTH - 40), 0)


class Player(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.image = pygame.image.load(os.path.join(BASE_DIR, "images", "Player.png"))
        self.rect = self.image.get_rect()
        self.rect.center = (160, 520)

    def move(self):
        pressed_keys = pygame.key.get_pressed()
        if self.rect.left > 0:
            if pressed_keys[K_LEFT]:
                self.rect.move_ip(-5, 0)
        if self.rect.right < SCREEN_WIDTH:
            if pressed_keys[K_RIGHT]:
                self.rect.move_ip(5, 0)


# ← ADDED: Coin class that spawns randomly and falls down
class Coin(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
        # Draw a yellow circle with black border as coin
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (10, 10), 10)
        pygame.draw.circle(self.image, BLACK, (10, 10), 10, 2)
        self.rect = self.image.get_rect()
        # Spawn at random x position at top of screen
        self.rect.center = (random.randint(20, SCREEN_WIDTH - 20), 0)

    def move(self):
        # Falls at 60% of enemy speed
        self.rect.move_ip(0, SPEED * 0.6)
        # Respawn at top if it goes off screen uncollected
        if self.rect.top > SCREEN_HEIGHT:
            self.rect.center = (random.randint(20, SCREEN_WIDTH - 20), 0)


#Setting up Sprites        
P1 = Player()
E1 = Enemy()

# ← ADDED: Create 1 coin on screen at a time
coin_list = [Coin() for _ in range(1)]

#Creating Sprite Groups
enemies = pygame.sprite.Group()
enemies.add(E1)

# ← ADDED: Coins sprite group
coins = pygame.sprite.Group()
for coin in coin_list:
    coins.add(coin)

all_sprites = pygame.sprite.Group()
all_sprites.add(P1)
all_sprites.add(E1)
# ← ADDED: Add coins to all_sprites so they get drawn
for coin in coin_list:
    all_sprites.add(coin)

#User event to increase speed every second
INC_SPEED = pygame.USEREVENT + 1
pygame.time.set_timer(INC_SPEED, 1000)

# -------------------- GAME LOOP --------------------
while True:

    for event in pygame.event.get():
        if event.type == INC_SPEED:
            SPEED += 0.5
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    DISPLAYSURF.blit(background, (0, 0))

    # Show score in top LEFT corner
    scores = font_small.render("Score: " + str(SCORE), True, BLACK)
    DISPLAYSURF.blit(scores, (10, 10))

    # ← ADDED: Show coin count in top RIGHT corner
    coin_text = font_small.render("Coins: " + str(COINS), True, YELLOW)
    DISPLAYSURF.blit(coin_text, (SCREEN_WIDTH - 100, 10))

    # Move and draw all sprites
    for entity in all_sprites:
        entity.move()
        DISPLAYSURF.blit(entity.image, entity.rect)

    # ← ADDED: Check if player collected a coin
    collected = pygame.sprite.spritecollide(P1, coins, False)  # type: ignore
    for coin in collected:
        COINS += 1
        # Respawn coin at new random position at top
        coin.rect.center = (random.randint(20, SCREEN_WIDTH - 20), 0)

    # Check collision with enemy
    if pygame.sprite.spritecollideany(P1, enemies):  # type: ignore
        pygame.mixer.music.stop()
        pygame.mixer.Sound(os.path.join(BASE_DIR, "music", "crash.wav")).play()
        time.sleep(1)

        DISPLAYSURF.fill(RED)
        DISPLAYSURF.blit(game_over, (30, 250))

        # ← ADDED: Show final coins on game over screen
        final_score = font_small.render("Score: " + str(SCORE) + "  Coins: " + str(COINS), True, BLACK)
        DISPLAYSURF.blit(final_score, (120, 350))

        pygame.display.update()
        for entity in all_sprites:
            entity.kill()
        time.sleep(2)
        pygame.quit()
        sys.exit()

    pygame.display.update()
    FramePerSec.tick(FPS)