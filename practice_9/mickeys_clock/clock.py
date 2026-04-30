import pygame
import datetime

def get_angles():
    now = datetime.datetime.now()
    
    # Minute hand: 6 degrees per minute
    min_ang = (now.minute * 6) - 90
    
    # Second hand: 6 degrees per second
    sec_ang = (now.second * 6) - 90
    
    return min_ang, sec_ang

def rotate_hand(surface, angle, center):
    rotated_surface = pygame.transform.rotate(surface, -angle)
    new_rect = rotated_surface.get_rect(center=center)
    return rotated_surface, new_rect