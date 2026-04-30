# ============================================================
#  paint.py  —  Paint App  (TSIS 2 Extended)
#  Run with:  python paint.py  (from inside the TSIS2/ folder)
#
#  New features over Practice 10-11:
#    • Pencil (freehand) tool
#    • Straight line tool with live preview
#    • Three brush sizes: S=2px (key 1), M=5px (key 2), L=10px (key 3)
#    • Flood-fill tool (click inside a closed region)
#    • Text tool: click to place, type, Enter=confirm, Esc=cancel
#    • Ctrl+S saves canvas as timestamped .png
#    • 8-colour palette
# ============================================================

import pygame       # Pygame library for window, events, drawing, and surfaces
import sys          # sys.exit() to close the program cleanly
import os           # os.path to locate this file and build paths
import datetime     # datetime.now() for generating timestamped save filenames

# Get the absolute path to the folder containing this script
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:               # Only add if it's not already there
    sys.path.insert(0, _HERE)           # Prepend so Python finds tools.py here first

# Import all drawing functions and constants from our tools module
from tools import (
    TOOLBAR_TOTAL_HEIGHT,           # Combined pixel height of both toolbar rows
    NAMED_COLORS,                   # List/set of valid colour name strings
    SIZE_LEVELS,                    # Available brush size options
    draw_toolbar,                   # Renders the full toolbar onto a surface
    get_tool_from_click,            # Returns which tool/colour/size was clicked
    get_solid_color,                # Converts a colour name string to an RGB tuple
    brush_px_from_key,              # Maps keyboard number (1/2/3) to pixel size
    draw_pencil_segment,            # Draws one freehand stroke segment
    draw_straight_line,             # Draws a straight line between two points
    draw_rectangle,                 # Draws an axis-aligned rectangle
    draw_square,                    # Draws a perfect square
    draw_circle,                    # Draws a circle by centre + radius
    draw_right_triangle,            # Draws a right-angled triangle
    draw_equilateral_triangle,      # Draws an equilateral triangle
    draw_rhombus,                   # Draws a diamond/rhombus shape
    erase,                          # Paints black to simulate erasing
    flood_fill,                     # Fills a bounded region with a colour
)

# ============================================================
#  Constants
# ============================================================
SCREEN_WIDTH  = 900     # Total window width in pixels
SCREEN_HEIGHT = 650     # Total window height in pixels
CANVAS_TOP    = TOOLBAR_TOTAL_HEIGHT    # Y coordinate where the drawable area starts (below toolbar)

# ============================================================
#  Pygame Init
# ============================================================
pygame.init()                                                       # Start all Pygame modules
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))    # Create the application window
pygame.display.set_caption("Paint App — TSIS 2 Extended")          # Set the window title bar text
clock  = pygame.time.Clock()                                        # Clock used to cap the frame rate

# Off-screen surface for the artwork — drawn to screen each frame
canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))  # Same size as the window
canvas.fill((0, 0, 0))                                  # Start with a black background
# Rect defining the drawable area — used to clip fill and eraser operations
canvas_rect = pygame.Rect(0, CANVAS_TOP, SCREEN_WIDTH, SCREEN_HEIGHT - CANVAS_TOP)

# ============================================================
#  App State
# ============================================================
mode        = 'pencil'  # Currently active tool
color_mode  = 'white'   # Currently active colour name
brush_size  = 2         # Active brush size in pixels (2 / 5 / 10)
drawing     = False     # True while the left mouse button is held down
start_pos   = (0, 0)    # Mouse position where the current drag started
prev_pos    = None      # Previous mouse position for continuous pencil/eraser strokes

# Text-tool state — all isolated here so it doesn't interfere with drawing tools
text_active  = False            # True when the user has clicked to place text
text_pos     = (0, 0)           # Pixel position where typed text will be drawn
text_buffer  = ""               # Characters typed so far, not yet committed to canvas
text_font    = pygame.font.SysFont("Courier", 20)   # Monospace font for text tool
cursor_timer = 0                # Millisecond counter used to create cursor blink effect

# ============================================================
#  Helpers
# ============================================================

def save_canvas():
    """Save canvas (cropped to drawing area) as a timestamped PNG."""
    ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")   # e.g. "20240501_143022"
    filename = f"canvas_{ts}.png"                                   # Unique filename per save
    sub = canvas.subsurface(canvas_rect)    # Crop to just the drawing area, excluding toolbar
    pygame.image.save(sub, filename)        # Write the surface pixels to a PNG file
    print(f"[Saved] {filename}")
    return filename


def draw_text_cursor(surf, pos, visible):
    """Draw a blinking cursor at the text insertion point."""
    if visible:                             # Only draw when the blink cycle is in the 'on' phase
        x, y = pos
        pygame.draw.line(surf, (255, 255, 255), (x, y), (x, y + 22), 2)    # White vertical bar, 22px tall


# ============================================================
#  Main Loop
# ============================================================
while True:

    dt = clock.tick(60)                             # Wait so the loop runs at most 60 times/sec; dt = elapsed ms
    cursor_timer = (cursor_timer + dt) % 1000       # Advance blink timer; wrap at 1000ms to repeat

    pressed   = pygame.key.get_pressed()                            # Snapshot of all currently held keys
    ctrl_held = pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL] # True if either Ctrl key is down
    alt_held  = pressed[pygame.K_LALT]  or pressed[pygame.K_RALT]  # True if either Alt key is down

    for event in pygame.event.get():    # Process every queued event this frame

        if event.type == pygame.QUIT:   # Window X button was clicked
            pygame.quit();  sys.exit()

        # ================================================================
        #  Keyboard
        # ================================================================
        if event.type == pygame.KEYDOWN:    # A key was just pressed this frame

            # --- Quit shortcuts ---
            if ((event.key == pygame.K_w  and ctrl_held) or    # Ctrl+W — close
                (event.key == pygame.K_F4 and alt_held)):       # Alt+F4 — close
                pygame.quit();  sys.exit()

            # --- Ctrl+S: save canvas to PNG ---
            if event.key == pygame.K_s and ctrl_held:
                if not text_active:     # Don't save while typing — 'S' might still be input
                    save_canvas()

            # === Text-tool input — intercept ALL keys when text mode is active ===
            if text_active:
                if event.key == pygame.K_RETURN:
                    # Commit the typed text permanently onto the canvas
                    surf = text_font.render(text_buffer, True,
                                            get_solid_color(color_mode))   # Render text with current colour
                    canvas.blit(surf, text_pos)     # Stamp text onto the canvas surface
                    text_active  = False            # Exit text mode
                    text_buffer  = ""               # Clear the buffer for next use
                elif event.key == pygame.K_ESCAPE:
                    text_active = False             # Cancel without committing anything
                    text_buffer = ""
                elif event.key == pygame.K_BACKSPACE:
                    text_buffer = text_buffer[:-1]  # Remove the last typed character
                else:
                    if event.unicode and event.unicode.isprintable():   # Filter out control characters
                        text_buffer += event.unicode    # Append the typed character to the buffer

            else:
                # === Normal (non-text) mode shortcuts ===
                if event.key == pygame.K_ESCAPE:    # Escape exits the app when not typing
                    pygame.quit();  sys.exit()

                # Map keyboard letters to colour names
                key_col = {
                    pygame.K_r: 'red',    pygame.K_g: 'green',
                    pygame.K_b: 'blue',   pygame.K_k: 'black',
                    pygame.K_w: 'white',  pygame.K_y: 'yellow',
                    pygame.K_o: 'orange', pygame.K_p: 'purple',
                }
                if event.key in key_col and not ctrl_held:  # Exclude Ctrl+W (quit) from colour shortcuts
                    color_mode = key_col[event.key]

                # Number keys 1/2/3 change brush size
                for key, num in ((pygame.K_1, 1), (pygame.K_2, 2), (pygame.K_3, 3)):
                    if event.key == key:
                        px = brush_px_from_key(num)     # Convert key number to actual pixel size
                        if px:
                            brush_size = px             # Apply the new size

        # ================================================================
        #  Mouse Down
        # ================================================================
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos                              # Unpack click coordinates
            toolbar_hit = get_tool_from_click(mx, my)      # Check if a toolbar element was clicked

            # --- Toolbar click ---
            if toolbar_hit is not None:
                if toolbar_hit.startswith("size_"):             # e.g. "size_5" means 5px brush
                    brush_size = int(toolbar_hit.split("_")[1]) # Parse the number after the underscore
                elif toolbar_hit in NAMED_COLORS:               # A colour swatch was clicked
                    color_mode = toolbar_hit
                else:
                    if text_active:             # Switching tools cancels any in-progress text
                        text_active = False
                        text_buffer = ""
                    mode    = toolbar_hit       # Switch to the clicked tool
                    drawing = False             # Reset drawing state for the new tool

            # --- Canvas click (left button only) ---
            elif my >= CANVAS_TOP and event.button == 1:

                if mode == 'text':
                    text_active = True          # Activate text input mode
                    text_pos    = (mx, my)      # Record where the text will be placed
                    text_buffer = ""            # Start with an empty buffer

                elif mode == 'fill':
                    # Flood-fill from the clicked pixel outward within canvas_rect bounds
                    flood_fill(canvas, (mx, my),
                               get_solid_color(color_mode), canvas_rect)

                elif mode == 'eraser':
                    drawing   = True
                    start_pos = (mx, my)
                    prev_pos  = (mx, my)
                    erase(canvas, (mx, my), brush_size, CANVAS_TOP)    # Erase immediately on first click

                elif mode == 'pencil':
                    drawing  = True
                    prev_pos = (mx, my)     # Start tracking from this position for smooth stroke

                else:
                    # All shape and line tools — record drag origin
                    drawing   = True
                    start_pos = (mx, my)
                    prev_pos  = (mx, my)

        # ================================================================
        #  Mouse Up
        # ================================================================
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:  # Left button released
            if drawing:
                mx, my = event.pos
                color  = get_solid_color(color_mode)    # Get the current colour as an RGB tuple

                # Commit the final shape to the canvas on mouse release
                if mode == 'line':
                    draw_straight_line(canvas, start_pos, (mx, my), color, brush_size)
                elif mode == 'rect':
                    draw_rectangle(canvas, start_pos, (mx, my), color, brush_size)
                elif mode == 'square':
                    draw_square(canvas, start_pos, (mx, my), color, brush_size)
                elif mode == 'circle':
                    draw_circle(canvas, start_pos, (mx, my), color, brush_size)
                elif mode == 'rtri':
                    draw_right_triangle(canvas, start_pos, (mx, my), color, brush_size)
                elif mode == 'etri':
                    draw_equilateral_triangle(canvas, start_pos, (mx, my), color, brush_size)
                elif mode == 'rhombus':
                    draw_rhombus(canvas, start_pos, (mx, my), color, brush_size)
                # pencil & eraser are painted continuously in MOUSEMOTION — nothing to commit here

                drawing  = False    # End the drag
                prev_pos = None     # Clear previous position so next stroke starts fresh

        # ================================================================
        #  Mouse Motion
        # ================================================================
        if event.type == pygame.MOUSEMOTION and drawing:    # Mouse moved while left button is held
            mx, my = event.pos
            if my >= CANVAS_TOP:            # Ignore motion over the toolbar area
                color = get_solid_color(color_mode)

                if mode == 'pencil' and prev_pos is not None:
                    draw_pencil_segment(canvas, prev_pos, (mx, my),
                                        color, brush_size)  # Draw segment from last position to current
                    prev_pos = (mx, my)     # Update previous position for the next segment

                elif mode == 'eraser' and prev_pos is not None:
                    erase(canvas, (mx, my), brush_size, CANVAS_TOP)    # Continuously erase as mouse moves
                    prev_pos = (mx, my)

    # ================================================================
    #  Render
    # ================================================================
    screen.blit(canvas, (0, 0))     # Draw the canvas onto the screen, covering the previous frame

    # Live shape / line previews — drawn on screen (not canvas) so they disappear if drag is cancelled
    if drawing and mode in ('line', 'rect', 'square', 'circle',
                             'rtri', 'etri', 'rhombus'):
        cur   = pygame.mouse.get_pos()          # Current mouse position for the preview endpoint
        color = get_solid_color(color_mode)
        if   mode == 'line':    draw_straight_line(screen, start_pos, cur, color, brush_size)
        elif mode == 'rect':    draw_rectangle(screen, start_pos, cur, color, brush_size)
        elif mode == 'square':  draw_square(screen, start_pos, cur, color, brush_size)
        elif mode == 'circle':  draw_circle(screen, start_pos, cur, color, brush_size)
        elif mode == 'rtri':    draw_right_triangle(screen, start_pos, cur, color, brush_size)
        elif mode == 'etri':    draw_equilateral_triangle(screen, start_pos, cur, color, brush_size)
        elif mode == 'rhombus': draw_rhombus(screen, start_pos, cur, color, brush_size)

    # Live text preview — shows typed characters before Enter commits them to canvas
    if text_active:
        preview = text_font.render(text_buffer, True, get_solid_color(color_mode))  # Render current buffer
        screen.blit(preview, text_pos)                              # Draw preview at the chosen position
        cursor_x = text_pos[0] + preview.get_width()               # Cursor sits right after the last character
        draw_text_cursor(screen, (cursor_x, text_pos[1]), cursor_timer < 500)   # On for first 500ms, off for second 500ms

    # Toolbar is drawn last so it always appears on top of canvas content
    draw_toolbar(screen, mode, color_mode, brush_size, SCREEN_WIDTH)

    pygame.display.flip()   # Push the completed frame to the monitor