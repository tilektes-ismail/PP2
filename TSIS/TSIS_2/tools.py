# ============================================================
#  tools.py  —  Paint App (TSIS 2)
#  Contains:
#    - All drawing functions (pen, pencil, line, rect, circle,
#      square, right triangle, equilateral triangle, rhombus,
#      eraser, fill, text)
#    - Toolbar rendering (two rows + size row)
#    - Toolbar click detection
# ============================================================

import pygame
import math
from collections import deque

# Toolbar layout constants
TOOLBAR_HEIGHT       = 50   # height of each row
TOOLBAR_TOTAL_HEIGHT = 150  # three rows total (tools, colours, sizes)


# ============================================================
#  Colour Helpers
# ============================================================

NAMED_COLORS = {
    'red':    (255,   0,   0),
    'green':  (  0, 200,   0),
    'blue':   (  0,   0, 255),
    'black':  (  0,   0,   0),
    'white':  (255, 255, 255),
    'yellow': (255, 220,   0),
    'orange': (255, 140,   0),
    'purple': (160,   0, 200),
}


def get_solid_color(color_mode):
    """Return an RGB tuple for the given color_mode string."""
    return NAMED_COLORS.get(color_mode, (0, 0, 255))


def get_gradient_color(index, color_mode):
    """Return a gradient colour based on index (0-255) for pen strokes."""
    c1 = max(0, min(255, 2 * index - 256))
    c2 = max(0, min(255, 2 * index))
    if color_mode == 'blue':
        return (c1, c1, c2)
    elif color_mode == 'red':
        return (c2, c1, c1)
    elif color_mode == 'green':
        return (c1, c2, c1)
    else:
        # For other colours fall back to solid
        return get_solid_color(color_mode)


# ============================================================
#  Toolbar Definition
# ============================================================

TOOLS = [
    ("Pencil",  "pencil",  10),
    ("Line",    "line",    90),
    ("Rect",    "rect",   170),
    ("Square",  "square", 250),
    ("Circle",  "circle", 330),
    ("RTri",    "rtri",   410),
    ("ETri",    "etri",   490),
    ("Rhombus", "rhombus",570),
    ("Eraser",  "eraser", 650),
    ("Fill",    "fill",   730),
    ("Text",    "text",   810),
]

COLOR_BUTTONS = [
    ("R", "red",    10),
    ("G", "green",  60),
    ("B", "blue",  110),
    ("K", "black", 160),
    ("W", "white", 210),
    ("Y", "yellow",260),
    ("O", "orange",310),
    ("P", "purple",360),
]

SIZE_LEVELS = [
    ("S (1)", 1,  2,  10),   # label, shortcut_key_num, px, x
    ("M (2)", 2,  5,  90),
    ("L (3)", 3, 10, 170),
]


def draw_toolbar(screen, mode, color_mode, brush_size, screen_width):
    """Render the three-row toolbar.
    Row 1 : tool buttons.
    Row 2 : colour buttons.
    Row 3 : brush-size buttons.
    """
    font = pygame.font.SysFont("Verdana", 11)
    small_font = pygame.font.SysFont("Verdana", 10)

    # ---- Row 1: tools ----
    pygame.draw.rect(screen, (50, 50, 50), (0, 0, screen_width, TOOLBAR_HEIGHT))
    for label, tool_mode, x in TOOLS:
        active = mode == tool_mode
        col = (255, 255, 100) if active else (160, 160, 160)
        pygame.draw.rect(screen, col, (x, 6, 72, 34), 0 if active else 2)
        txt_col = (0, 0, 0) if active else (200, 200, 200)
        text = font.render(label, True, txt_col)
        screen.blit(text, (x + 4, 18))

    # ---- Row 2: colours ----
    row2_y = TOOLBAR_HEIGHT
    pygame.draw.rect(screen, (30, 30, 30), (0, row2_y, screen_width, TOOLBAR_HEIGHT))
    for label, col, x in COLOR_BUTTONS:
        rgb = NAMED_COLORS[col]
        active = color_mode == col
        pygame.draw.rect(screen, rgb, (x, row2_y + 8, 40, 34))
        if active:
            pygame.draw.rect(screen, (255, 255, 255), (x, row2_y + 8, 40, 34), 3)
        text = font.render(label, True,
                           (0, 0, 0) if sum(rgb) > 380 else (255, 255, 255))
        screen.blit(text, (x + 13, row2_y + 18))

    # Hint for colour row
    hint = small_font.render("Keys: r g b k w y o p", True, (100, 100, 100))
    screen.blit(hint, (420, row2_y + 18))

    # ---- Row 3: brush sizes ----
    row3_y = TOOLBAR_HEIGHT * 2
    pygame.draw.rect(screen, (40, 40, 40), (0, row3_y, screen_width, TOOLBAR_HEIGHT))
    size_label = small_font.render("Brush size:", True, (180, 180, 180))
    screen.blit(size_label, (10, row3_y + 18))
    for label, key_num, px, x in SIZE_LEVELS:
        active = brush_size == px
        col = (255, 220, 80) if active else (120, 120, 120)
        pygame.draw.rect(screen, col, (x + 80, row3_y + 6, 72, 34), 0 if active else 2)
        txt_col = (0, 0, 0) if active else (200, 200, 200)
        text = font.render(label, True, txt_col)
        screen.blit(text, (x + 84, row3_y + 17))

    # Ctrl+S hint on far right
    hint2 = small_font.render("Ctrl+S = save PNG", True, (100, 100, 100))
    screen.blit(hint2, (screen_width - 160, row3_y + 18))


def get_tool_from_click(x, y):
    """Return the tool/colour/size string that was clicked, or None."""
    if 0 <= y < TOOLBAR_HEIGHT:
        for label, tool_mode, tx in TOOLS:
            if tx <= x <= tx + 72:
                return tool_mode

    if TOOLBAR_HEIGHT <= y < TOOLBAR_HEIGHT * 2:
        for label, col, cx in COLOR_BUTTONS:
            if cx <= x <= cx + 40:
                return col

    if TOOLBAR_HEIGHT * 2 <= y < TOOLBAR_TOTAL_HEIGHT:
        for label, key_num, px, tx in SIZE_LEVELS:
            if (tx + 80) <= x <= (tx + 152):
                return f"size_{px}"

    return None


def brush_px_from_key(key_num):
    """Map keyboard digit 1/2/3 → brush pixel size."""
    mapping = {1: 2, 2: 5, 3: 10}
    return mapping.get(key_num)


# ============================================================
#  Drawing Functions
# ============================================================

def draw_pencil_segment(screen, start, end, color, width):
    """Draw a single freehand pencil segment between two points."""
    if start == end:
        pygame.draw.circle(screen, color, start, max(1, width // 2))
        return
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    iterations = max(abs(dx), abs(dy), 1)
    half = max(1, width // 2)
    for i in range(iterations + 1):
        t = i / iterations
        x = int(start[0] + t * dx)
        y = int(start[1] + t * dy)
        pygame.draw.circle(screen, color, (x, y), half)


def draw_straight_line(screen, start, end, color, width):
    """Draw a straight line with given width."""
    pygame.draw.line(screen, color, start, end, max(1, width))


def draw_rectangle(screen, start, end, color, outline):
    x = min(start[0], end[0])
    y = min(start[1], end[1])
    w = abs(end[0] - start[0])
    h = abs(end[1] - start[1])
    if w > 0 and h > 0:
        pygame.draw.rect(screen, color, (x, y, w, h), outline)


def draw_square(screen, start, end, color, outline):
    dx   = end[0] - start[0]
    dy   = end[1] - start[1]
    side = min(abs(dx), abs(dy))
    x = start[0] if dx >= 0 else start[0] - side
    y = start[1] if dy >= 0 else start[1] - side
    if side > 0:
        pygame.draw.rect(screen, color, (x, y, side, side), outline)


def draw_circle(screen, start, end, color, outline):
    r = int(math.hypot(end[0] - start[0], end[1] - start[1]))
    if r > 0:
        pygame.draw.circle(screen, color, start, r, outline)


def draw_right_triangle(screen, start, end, color, outline):
    A = (start[0], start[1])
    B = (start[0], end[1])
    C = (end[0],   end[1])
    pygame.draw.polygon(screen, color, [A, B, C], outline)


def draw_equilateral_triangle(screen, start, end, color, outline):
    base = abs(end[0] - start[0])
    if base == 0:
        return
    height = int(base * math.sqrt(3) / 2)
    left   = (min(start[0], end[0]), start[1])
    right  = (max(start[0], end[0]), start[1])
    apex   = ((left[0] + right[0]) // 2, start[1] - height)
    pygame.draw.polygon(screen, color, [left, right, apex], outline)


def draw_rhombus(screen, start, end, color, outline):
    x_min = min(start[0], end[0]);  x_max = max(start[0], end[0])
    y_min = min(start[1], end[1]);  y_max = max(start[1], end[1])
    cx = (x_min + x_max) // 2;     cy = (y_min + y_max) // 2
    pts = [(cx, y_min), (x_max, cy), (cx, y_max), (x_min, cy)]
    pygame.draw.polygon(screen, color, pts, outline)


def erase(screen, position, size, canvas_top):
    """Erase by painting a white circle (or black if preferred)."""
    if position[1] >= canvas_top:
        pygame.draw.circle(screen, (0, 0, 0), position, size * 2)


# ============================================================
#  Flood Fill
# ============================================================

def flood_fill(surface, pos, fill_color, canvas_rect):
    """BFS flood fill on a pygame Surface.
    Only fills inside canvas_rect to avoid touching the toolbar.
    """
    x, y = pos
    if not canvas_rect.collidepoint(x, y):
        return

    # Lock the surface for direct pixel access
    surface.lock()
    target_color = surface.get_at((x, y))[:3]
    fill_rgb     = fill_color[:3] if len(fill_color) == 4 else fill_color

    if target_color == fill_rgb:
        surface.unlock()
        return

    w, h = surface.get_size()
    top  = canvas_rect.top
    visited = set()
    queue = deque()
    queue.append((x, y))
    visited.add((x, y))

    while queue:
        cx, cy = queue.popleft()
        if not (0 <= cx < w and top <= cy < h):
            continue
        if surface.get_at((cx, cy))[:3] != target_color:
            continue
        surface.set_at((cx, cy), fill_rgb)
        for nx, ny in ((cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)):
            if (nx, ny) not in visited and 0 <= nx < w and top <= ny < h:
                visited.add((nx, ny))
                queue.append((nx, ny))

    surface.unlock()
