# ============================================================
#  main.py  —  Paint App (Entry Point)
#  Run with:  python main.py  (from inside the paint/ folder)
# ============================================================

import pygame       # Pygame library for window, events, and drawing
import sys          # sys.exit() to close the program cleanly
import os           # os.path to locate this file on disk

# Insert this file's directory into the module search path so Python finds drawing_tools.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import everything needed from drawing_tools
from drawing_tools import (
    TOOLBAR_TOTAL_HEIGHT,           # Combined height of both toolbar rows (100px)
    draw_toolbar,                   # Renders the toolbar onto the screen
    get_tool_from_click,            # Returns which tool/color was clicked
    drawLineBetween,                # Draws a smooth pen stroke segment
    draw_rectangle,                 # Draws a rectangle
    draw_square,                    # Draws a perfect square
    draw_circle,                    # Draws a circle
    draw_right_triangle,            # Draws a right-angled triangle
    draw_equilateral_triangle,      # Draws an equilateral triangle
    draw_rhombus,                   # Draws a diamond/rhombus
    erase,                          # Erases by painting black circles
)

# ============================================================
#  Constants
# ============================================================
SCREEN_WIDTH  = 800     # Window width in pixels
SCREEN_HEIGHT = 580     # Window height in pixels
CANVAS_TOP    = TOOLBAR_TOTAL_HEIGHT   # Y coordinate where the drawable canvas begins (below toolbar)

# ============================================================
#  Pygame Init
# ============================================================
pygame.init()                                                       # Initialize all Pygame modules
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))    # Create the main window
pygame.display.set_caption("Paint App — Extended")                 # Set the window title bar text
clock = pygame.time.Clock()                                         # Clock used to cap FPS

# ============================================================
#  Canvas — separate surface so toolbar never dirties artwork
# ============================================================
canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))  # Off-screen surface the same size as the window
canvas.fill((0, 0, 0))                                  # Fill canvas with black (blank drawing area)

# ============================================================
#  App State
# ============================================================
radius     = 15         # Current brush/eraser size in pixels
mode       = 'pen'      # Active tool; starts as pen
color_mode = 'blue'     # Active colour; starts as blue
points     = []         # Buffer of mouse positions for the current pen stroke
drawing    = False      # True while the left mouse button is held down
start_pos  = (0, 0)     # Mouse position where the current drag started

# ============================================================
#  Main Loop
# ============================================================
while True:

    pressed   = pygame.key.get_pressed()                            # Snapshot of all currently held keys
    alt_held  = pressed[pygame.K_LALT]  or pressed[pygame.K_RALT]  # True if either Alt key is down
    ctrl_held = pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL] # True if either Ctrl key is down

    for event in pygame.event.get():    # Process every event that happened this frame

        if event.type == pygame.QUIT:   # User clicked the window's X button
            pygame.quit()               # Shut down all Pygame modules
            sys.exit()                  # Terminate the Python process

        # ---- Keyboard shortcuts ----
        if event.type == pygame.KEYDOWN:                            # A key was just pressed
            if ((event.key == pygame.K_w  and ctrl_held) or        # Ctrl+W — close
                (event.key == pygame.K_F4 and alt_held)  or        # Alt+F4 — close
                 event.key == pygame.K_ESCAPE):                     # Escape — close
                pygame.quit()
                sys.exit()
            if   event.key == pygame.K_r: color_mode = 'red'       # R key — switch to red
            elif event.key == pygame.K_g: color_mode = 'green'     # G key — switch to green
            elif event.key == pygame.K_b: color_mode = 'blue'      # B key — switch to blue

        # ---- Mouse down ----
        if event.type == pygame.MOUSEBUTTONDOWN:            # A mouse button was just pressed
            click_x, click_y = event.pos                   # Unpack the click coordinates
            toolbar_hit = get_tool_from_click(click_x, click_y)  # Check if a toolbar button was hit

            if toolbar_hit in ('pen', 'rect', 'square', 'circle',
                               'rtri', 'etri', 'rhombus', 'eraser'):
                mode   = toolbar_hit    # Switch active tool to whatever was clicked
                points = []             # Clear any leftover pen points from before

            elif toolbar_hit in ('red', 'green', 'blue'):
                color_mode = toolbar_hit    # Switch active colour to whatever was clicked

            elif click_y > CANVAS_TOP:      # Click landed on the canvas (below the toolbar)
                if event.button == 1:                           # Left click
                    radius    = min(200, radius + 1)            # Increase brush size, cap at 200
                    drawing   = True                            # Start a drag
                    start_pos = event.pos                       # Record drag origin
                    if mode == 'eraser':                        # Eraser acts immediately on click
                        erase(canvas, event.pos, radius)        # Erase at click position right away
                elif event.button == 3:                         # Right click
                    radius = max(1, radius - 1)                 # Decrease brush size, floor at 1

        # ---- Mouse up ----
        if event.type == pygame.MOUSEBUTTONUP:          # A mouse button was just released
            if event.button == 1 and drawing:           # Only handle left button release while dragging
                drawing = False                         # End the drag
                if mode == 'rect':                      # Commit a rectangle to the canvas
                    draw_rectangle(canvas, start_pos, event.pos, color_mode, 2)
                elif mode == 'square':                  # Commit a square to the canvas
                    draw_square(canvas, start_pos, event.pos, color_mode, 2)
                elif mode == 'circle':                  # Commit a circle to the canvas
                    draw_circle(canvas, start_pos, event.pos, color_mode, 2)
                elif mode == 'rtri':                    # Commit a right triangle to the canvas
                    draw_right_triangle(canvas, start_pos, event.pos, color_mode, 2)
                elif mode == 'etri':                    # Commit an equilateral triangle to the canvas
                    draw_equilateral_triangle(canvas, start_pos, event.pos, color_mode, 2)
                elif mode == 'rhombus':                 # Commit a rhombus to the canvas
                    draw_rhombus(canvas, start_pos, event.pos, color_mode, 2)
                elif mode == 'pen':                     # Commit the recorded pen stroke to the canvas
                    for i in range(len(points) - 1):    # Step through each consecutive pair of points
                        drawLineBetween(canvas, i, points[i], points[i + 1],
                                        radius, color_mode)  # Draw segment between point i and i+1
                    points = []     # Clear the point buffer after committing

        # ---- Mouse motion ----
        if event.type == pygame.MOUSEMOTION and drawing:    # Mouse moved while left button is held
            if event.pos[1] > CANVAS_TOP:                  # Ignore motion over the toolbar
                if mode == 'pen':
                    points = (points + [event.pos])[-256:]  # Append new point, keep last 256 max
                elif mode == 'eraser':
                    erase(canvas, event.pos, radius)        # Erase continuously as mouse moves

    # ---- Render ----
    screen.blit(canvas, (0, 0))     # Copy the canvas onto the screen starting at top-left

    # Live pen preview — draw the in-progress stroke directly on screen (not canvas yet)
    if mode == 'pen':
        for i in range(len(points) - 1):    # Loop through buffered stroke points
            drawLineBetween(screen, i, points[i], points[i + 1], radius, color_mode)  # Draw preview segment

    # Live shape preview — show the shape outline while the user is still dragging
    if drawing and mode in ('rect', 'square', 'circle', 'rtri', 'etri', 'rhombus'):
        cur = pygame.mouse.get_pos()                                            # Get current mouse position
        if   mode == 'rect':    draw_rectangle(screen, start_pos, cur, color_mode, 2)          # Preview rectangle
        elif mode == 'square':  draw_square(screen, start_pos, cur, color_mode, 2)             # Preview square
        elif mode == 'circle':  draw_circle(screen, start_pos, cur, color_mode, 2)             # Preview circle
        elif mode == 'rtri':    draw_right_triangle(screen, start_pos, cur, color_mode, 2)     # Preview right triangle
        elif mode == 'etri':    draw_equilateral_triangle(screen, start_pos, cur, color_mode, 2) # Preview equilateral triangle
        elif mode == 'rhombus': draw_rhombus(screen, start_pos, cur, color_mode, 2)            # Preview rhombus

    # Toolbar always on top — drawn last so it covers any canvas content beneath it
    draw_toolbar(screen, mode, color_mode, SCREEN_WIDTH)

    pygame.display.flip()   # Push the completed frame to the monitor
    clock.tick(60)          # Wait so the loop runs at most 60 times per second