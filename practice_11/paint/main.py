# ============================================================
#  main.py  —  Paint App (Entry Point)
#  Run with:  python main.py  (from inside the paint/ folder)
# ============================================================

import pygame
import sys
import os

# Make sure Python finds drawing_tools in the same folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from drawing_tools import (
    TOOLBAR_TOTAL_HEIGHT,
    draw_toolbar,
    get_tool_from_click,
    drawLineBetween,
    draw_rectangle,
    draw_square,
    draw_circle,
    draw_right_triangle,
    draw_equilateral_triangle,
    draw_rhombus,
    erase,
)

# ============================================================
#  Constants
# ============================================================
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 580
CANVAS_TOP    = TOOLBAR_TOTAL_HEIGHT   # Canvas starts below both toolbar rows

# ============================================================
#  Pygame Init
# ============================================================
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Paint App — Extended")
clock = pygame.time.Clock()

# ============================================================
#  Canvas — separate surface so toolbar never dirties artwork
# ============================================================
canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
canvas.fill((0, 0, 0))

# ============================================================
#  App State
# ============================================================
radius     = 15
mode       = 'pen'
color_mode = 'blue'
points     = []
drawing    = False
start_pos  = (0, 0)

# ============================================================
#  Main Loop
# ============================================================
while True:

    pressed   = pygame.key.get_pressed()
    alt_held  = pressed[pygame.K_LALT]  or pressed[pygame.K_RALT]
    ctrl_held = pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # ---- Keyboard shortcuts ----
        if event.type == pygame.KEYDOWN:
            if ((event.key == pygame.K_w  and ctrl_held) or
                (event.key == pygame.K_F4 and alt_held)  or
                 event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            if   event.key == pygame.K_r: color_mode = 'red'
            elif event.key == pygame.K_g: color_mode = 'green'
            elif event.key == pygame.K_b: color_mode = 'blue'

        # ---- Mouse down ----
        if event.type == pygame.MOUSEBUTTONDOWN:
            click_x, click_y = event.pos
            toolbar_hit = get_tool_from_click(click_x, click_y)

            if toolbar_hit in ('pen', 'rect', 'square', 'circle',
                               'rtri', 'etri', 'rhombus', 'eraser'):
                mode   = toolbar_hit
                points = []

            elif toolbar_hit in ('red', 'green', 'blue'):
                color_mode = toolbar_hit

            elif click_y > CANVAS_TOP:
                if event.button == 1:
                    radius    = min(200, radius + 1)
                    drawing   = True
                    start_pos = event.pos
                    # Erase immediately on first click
                    if mode == 'eraser':
                        erase(canvas, event.pos, radius)
                elif event.button == 3:
                    radius = max(1, radius - 1)

        # ---- Mouse up ----
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and drawing:
                drawing = False
                if mode == 'rect':
                    draw_rectangle(canvas, start_pos, event.pos, color_mode, 2)
                elif mode == 'square':
                    draw_square(canvas, start_pos, event.pos, color_mode, 2)
                elif mode == 'circle':
                    draw_circle(canvas, start_pos, event.pos, color_mode, 2)
                elif mode == 'rtri':
                    draw_right_triangle(canvas, start_pos, event.pos, color_mode, 2)
                elif mode == 'etri':
                    draw_equilateral_triangle(canvas, start_pos, event.pos, color_mode, 2)
                elif mode == 'rhombus':
                    draw_rhombus(canvas, start_pos, event.pos, color_mode, 2)
                elif mode == 'pen':
                    for i in range(len(points) - 1):
                        drawLineBetween(canvas, i, points[i], points[i + 1],
                                        radius, color_mode)
                    points = []

        # ---- Mouse motion ----
        if event.type == pygame.MOUSEMOTION and drawing:
            if event.pos[1] > CANVAS_TOP:
                if mode == 'pen':
                    points = (points + [event.pos])[-256:]
                elif mode == 'eraser':
                    erase(canvas, event.pos, radius)

    # ---- Render ----
    screen.blit(canvas, (0, 0))

    # Live pen preview
    if mode == 'pen':
        for i in range(len(points) - 1):
            drawLineBetween(screen, i, points[i], points[i + 1], radius, color_mode)

    # Live shape preview while dragging
    if drawing and mode in ('rect', 'square', 'circle', 'rtri', 'etri', 'rhombus'):
        cur = pygame.mouse.get_pos()
        if   mode == 'rect':    draw_rectangle(screen, start_pos, cur, color_mode, 2)
        elif mode == 'square':  draw_square(screen, start_pos, cur, color_mode, 2)
        elif mode == 'circle':  draw_circle(screen, start_pos, cur, color_mode, 2)
        elif mode == 'rtri':    draw_right_triangle(screen, start_pos, cur, color_mode, 2)
        elif mode == 'etri':    draw_equilateral_triangle(screen, start_pos, cur, color_mode, 2)
        elif mode == 'rhombus': draw_rhombus(screen, start_pos, cur, color_mode, 2)

    # Toolbar always on top
    draw_toolbar(screen, mode, color_mode, SCREEN_WIDTH)

    pygame.display.flip()
    clock.tick(60)
