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

import pygame
import sys
import os
import datetime

# Ensure Python finds tools.py in the same folder as this file,
# regardless of where the script is launched from.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from tools import (
    TOOLBAR_TOTAL_HEIGHT,
    NAMED_COLORS,
    SIZE_LEVELS,
    draw_toolbar,
    get_tool_from_click,
    get_solid_color,
    brush_px_from_key,
    draw_pencil_segment,
    draw_straight_line,
    draw_rectangle,
    draw_square,
    draw_circle,
    draw_right_triangle,
    draw_equilateral_triangle,
    draw_rhombus,
    erase,
    flood_fill,
)

# ============================================================
#  Constants
# ============================================================
SCREEN_WIDTH  = 900
SCREEN_HEIGHT = 650
CANVAS_TOP    = TOOLBAR_TOTAL_HEIGHT

# ============================================================
#  Pygame Init
# ============================================================
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Paint App — TSIS 2 Extended")
clock  = pygame.time.Clock()

# Separate canvas surface so toolbar never smears artwork
canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
canvas.fill((0, 0, 0))
canvas_rect = pygame.Rect(0, CANVAS_TOP, SCREEN_WIDTH, SCREEN_HEIGHT - CANVAS_TOP)

# ============================================================
#  App State
# ============================================================
mode        = 'pencil'
color_mode  = 'white'
brush_size  = 2           # active brush pixel size (2 / 5 / 10)
drawing     = False
start_pos   = (0, 0)
prev_pos    = None        # for freehand pencil between frames

# Text-tool state
text_active  = False
text_pos     = (0, 0)
text_buffer  = ""
text_font    = pygame.font.SysFont("Courier", 20)
cursor_timer = 0          # for blinking cursor

# ============================================================
#  Helpers
# ============================================================

def save_canvas():
    """Save canvas (cropped to drawing area) as a timestamped PNG."""
    ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"canvas_{ts}.png"
    # Save just the canvas area (without toolbar)
    sub = canvas.subsurface(canvas_rect)
    pygame.image.save(sub, filename)
    print(f"[Saved] {filename}")
    return filename


def draw_text_cursor(surf, pos, visible):
    """Draw a blinking cursor at the text insertion point."""
    if visible:
        x, y = pos
        pygame.draw.line(surf, (255, 255, 255), (x, y), (x, y + 22), 2)


# ============================================================
#  Main Loop
# ============================================================
while True:

    dt = clock.tick(60)
    cursor_timer = (cursor_timer + dt) % 1000   # blink every 1 s

    pressed   = pygame.key.get_pressed()
    ctrl_held = pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]
    alt_held  = pressed[pygame.K_LALT]  or pressed[pygame.K_RALT]

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit();  sys.exit()

        # ================================================================
        #  Keyboard
        # ================================================================
        if event.type == pygame.KEYDOWN:

            # --- Quit shortcuts ---
            if ((event.key == pygame.K_w  and ctrl_held) or
                (event.key == pygame.K_F4 and alt_held)):
                pygame.quit();  sys.exit()

            # --- Ctrl+S: save ---
            if event.key == pygame.K_s and ctrl_held:
                if not text_active:
                    save_canvas()

            # === Text-tool input ===
            if text_active:
                if event.key == pygame.K_RETURN:
                    # Commit text to canvas
                    surf = text_font.render(text_buffer, True,
                                            get_solid_color(color_mode))
                    canvas.blit(surf, text_pos)
                    text_active  = False
                    text_buffer  = ""
                elif event.key == pygame.K_ESCAPE:
                    text_active = False
                    text_buffer = ""
                elif event.key == pygame.K_BACKSPACE:
                    text_buffer = text_buffer[:-1]
                else:
                    # Accept printable characters
                    if event.unicode and event.unicode.isprintable():
                        text_buffer += event.unicode
            else:
                # === Normal mode shortcuts ===
                # Escape closes app in non-text mode
                if event.key == pygame.K_ESCAPE:
                    pygame.quit();  sys.exit()

                # Colour keys
                key_col = {
                    pygame.K_r: 'red',   pygame.K_g: 'green',
                    pygame.K_b: 'blue',  pygame.K_k: 'black',
                    pygame.K_w: 'white', pygame.K_y: 'yellow',
                    pygame.K_o: 'orange',pygame.K_p: 'purple',
                }
                if event.key in key_col and not ctrl_held:
                    color_mode = key_col[event.key]

                # Brush size keys 1 / 2 / 3
                for key, num in ((pygame.K_1, 1), (pygame.K_2, 2), (pygame.K_3, 3)):
                    if event.key == key:
                        px = brush_px_from_key(num)
                        if px:
                            brush_size = px

        # ================================================================
        #  Mouse Down
        # ================================================================
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            toolbar_hit = get_tool_from_click(mx, my)

            # --- Toolbar click ---
            if toolbar_hit is not None:
                if toolbar_hit.startswith("size_"):
                    brush_size = int(toolbar_hit.split("_")[1])
                elif toolbar_hit in NAMED_COLORS:
                    color_mode = toolbar_hit
                else:
                    # Switching tools cancels text input
                    if text_active:
                        text_active = False
                        text_buffer = ""
                    mode    = toolbar_hit
                    drawing = False

            # --- Canvas click ---
            elif my >= CANVAS_TOP and event.button == 1:

                if mode == 'text':
                    # Start text insertion
                    text_active = True
                    text_pos    = (mx, my)
                    text_buffer = ""

                elif mode == 'fill':
                    flood_fill(canvas, (mx, my),
                               get_solid_color(color_mode), canvas_rect)

                elif mode == 'eraser':
                    drawing   = True
                    start_pos = (mx, my)
                    prev_pos  = (mx, my)
                    erase(canvas, (mx, my), brush_size, CANVAS_TOP)

                elif mode == 'pencil':
                    drawing  = True
                    prev_pos = (mx, my)

                else:
                    # Shape / line tools
                    drawing   = True
                    start_pos = (mx, my)
                    prev_pos  = (mx, my)

        # ================================================================
        #  Mouse Up
        # ================================================================
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if drawing:
                mx, my = event.pos
                color  = get_solid_color(color_mode)

                if mode == 'line':
                    draw_straight_line(canvas, start_pos, (mx, my),
                                       color, brush_size)
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
                # pencil & eraser: already painted in MOUSEMOTION

                drawing  = False
                prev_pos = None

        # ================================================================
        #  Mouse Motion
        # ================================================================
        if event.type == pygame.MOUSEMOTION and drawing:
            mx, my = event.pos
            if my >= CANVAS_TOP:
                color = get_solid_color(color_mode)

                if mode == 'pencil' and prev_pos is not None:
                    draw_pencil_segment(canvas, prev_pos, (mx, my),
                                        color, brush_size)
                    prev_pos = (mx, my)

                elif mode == 'eraser' and prev_pos is not None:
                    erase(canvas, (mx, my), brush_size, CANVAS_TOP)
                    prev_pos = (mx, my)

    # ================================================================
    #  Render
    # ================================================================
    screen.blit(canvas, (0, 0))

    # Live shape / line previews while dragging
    if drawing and mode in ('line', 'rect', 'square', 'circle',
                             'rtri', 'etri', 'rhombus'):
        cur   = pygame.mouse.get_pos()
        color = get_solid_color(color_mode)
        if   mode == 'line':    draw_straight_line(screen, start_pos, cur, color, brush_size)
        elif mode == 'rect':    draw_rectangle(screen, start_pos, cur, color, brush_size)
        elif mode == 'square':  draw_square(screen, start_pos, cur, color, brush_size)
        elif mode == 'circle':  draw_circle(screen, start_pos, cur, color, brush_size)
        elif mode == 'rtri':    draw_right_triangle(screen, start_pos, cur, color, brush_size)
        elif mode == 'etri':    draw_equilateral_triangle(screen, start_pos, cur, color, brush_size)
        elif mode == 'rhombus': draw_rhombus(screen, start_pos, cur, color, brush_size)

    # Live text preview
    if text_active:
        preview = text_font.render(text_buffer, True, get_solid_color(color_mode))
        screen.blit(preview, text_pos)
        # Blink cursor
        cursor_x = text_pos[0] + preview.get_width()
        draw_text_cursor(screen, (cursor_x, text_pos[1]), cursor_timer < 500)

    # Toolbar always on top
    draw_toolbar(screen, mode, color_mode, brush_size, SCREEN_WIDTH)

    pygame.display.flip()