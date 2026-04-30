import pygame
import sys
import math
from clock import get_angles, rotate_hand

pygame.init()
SIZE = 800
screen = pygame.display.set_mode((SIZE, SIZE))
pygame.display.set_caption("Mickey's Minutes & Seconds Clock")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 45, bold=True)

# Colors
BLACK, WHITE = (0, 0, 0), (255, 255, 255)
RED, YELLOW = (200, 0, 0), (255, 220, 0)
SKIN, CREAM = (255, 220, 180), (245, 245, 220)

# Create Hand Surface
def create_hand(length):
    surf = pygame.Surface((length, 60), pygame.SRCALPHA)
    pygame.draw.rect(surf, BLACK, (0, 25, length - 60, 12)) 
    pygame.draw.ellipse(surf, WHITE, (length - 80, 10, 80, 50)) 
    pygame.draw.ellipse(surf, BLACK, (length - 80, 10, 80, 50), 3)
    return surf

# Two hands only
hand_surf = create_hand(320)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    min_ang, sec_ang = get_angles()
    screen.fill(CREAM)

    center_x, center_y = SIZE // 2, SIZE // 2
    
    # 1. DRAW NUMBERS
    pygame.draw.circle(screen, BLACK, (center_x, center_y), 385, 5)
    for i in range(1, 13):
        angle_rad = math.radians(i * 30 - 90)
        num_x = center_x + 335 * math.cos(angle_rad)
        num_y = center_y + 335 * math.sin(angle_rad)
        num_text = font.render(str(i), True, BLACK)
        screen.blit(num_text, num_text.get_rect(center=(int(num_x), int(num_y))))

    # 2. POSITION MICKEY HIGHER
    mk_x, mk_y = center_x, center_y - 90 

    # Mickey Body Parts
    pygame.draw.ellipse(screen, YELLOW, (mk_x-140, mk_y+300, 100, 60)) 
    pygame.draw.ellipse(screen, YELLOW, (mk_x+40, mk_y+300, 100, 60))  
    pygame.draw.rect(screen, BLACK, (mk_x-100, mk_y+240, 15, 70))      
    pygame.draw.rect(screen, BLACK, (mk_x+85, mk_y+240, 15, 70))       
    pygame.draw.ellipse(screen, RED, (mk_x-100, mk_y+140, 200, 130))  
    pygame.draw.circle(screen, WHITE, (mk_x-40, mk_y+200), 12)        
    pygame.draw.circle(screen, WHITE, (mk_x+40, mk_y+200), 12) 
    pygame.draw.ellipse(screen, BLACK, (mk_x-60, mk_y+80, 120, 100))  
    pygame.draw.circle(screen, BLACK, (mk_x-110, mk_y-90), 75)        
    pygame.draw.circle(screen, BLACK, (mk_x+110, mk_y-90), 75) 
    pygame.draw.circle(screen, BLACK, (mk_x, mk_y), 100)              
    pygame.draw.ellipse(screen, SKIN, (mk_x-80, mk_y-40, 160, 130))   
    pygame.draw.circle(screen, WHITE, (mk_x-30, mk_y-20), 15)         
    pygame.draw.circle(screen, WHITE, (mk_x+30, mk_y-20), 15) 
    pygame.draw.circle(screen, BLACK, (mk_x, mk_y+10), 10)            

    # 3. DRAW ONLY TWO HANDS
    pivot = (mk_x, mk_y + 50)
    
    # Right Hand = Minutes
    m_img, m_rect = rotate_hand(hand_surf, min_ang, pivot)
    screen.blit(m_img, m_rect)
    
    # Left Hand = Seconds
    s_img, s_rect = rotate_hand(hand_surf, sec_ang, pivot)
    screen.blit(s_img, s_rect)

    pygame.display.flip()
    clock.tick(60)